import json
import os
import time
from typing import TypedDict

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

AGENTS = ("macro", "sector", "interest")
MAX_ATTEMPTS = 2
MAX_API_RETRIES = 1
REQUEST_TIMEOUT_MS = 8000
RETRY_DELAY_SECONDS = 1
SUPERVISOR_MODEL = os.getenv("FINSIGHT_SUPERVISOR_MODEL", "gemini-3.1-flash-lite")


class GraphState(TypedDict, total=False):
    news_data: list
    market_data: list
    interest_candidates: list
    macro_analysis: str
    sector_analysis: str
    interest_analysis: str
    final_summary: str
    next_agent: str
    supervisor_reason: str
    decision_source: str
    agent_attempts: dict[str, int]
    routing_log: list[dict]
    quality_feedback: dict[str, str]
    agent_status: dict[str, str]
    agent_errors: dict[str, str]
    supervisor_llm_disabled: bool


def get_available_agents(state: GraphState) -> list[str]:
    attempts = state.get("agent_attempts", {})
    return [agent for agent in AGENTS if attempts.get(agent, 0) < MAX_ATTEMPTS]


def get_pending_agents(state: GraphState) -> list[str]:
    attempts = state.get("agent_attempts", {})
    return [agent for agent in AGENTS if attempts.get(agent, 0) == 0]


def get_quality_issues(state: GraphState) -> dict[str, str]:
    attempts = state.get("agent_attempts", {})
    statuses = state.get("agent_status", {})
    errors = state.get("agent_errors", {})
    issues = {}
    for agent in AGENTS:
        if attempts.get(agent, 0) == 0:
            continue
        status = statuses.get(agent)
        analysis = state.get(f"{agent}_analysis", "")
        if status in ("fallback", "error"):
            detail = errors.get(agent, "원인을 확인할 수 없습니다.")
            issues[agent] = f"Agent 실행 상태: {status}. 원인: {detail}"
        elif not isinstance(analysis, str) or not analysis.strip():
            issues[agent] = "분석 결과가 비어 있습니다."
    return issues


def call_supervisor_llm(context: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    prompt = (
        "당신은 FinSight 금융 분석 Supervisor입니다.\n"
        "분석 상태를 검토하고 다음 Agent를 결정하세요.\n"
        "available_agents 중 하나만 선택할 수 있습니다.\n"
        "pending_agents가 남아 있다면 반드시 그중 하나를 선택하세요.\n"
        "pending_agents가 없다면 기존 분석의 품질을 평가하세요.\n"
        "근거가 부족하거나 모순이 있으면 재분석할 Agent를 선택하세요.\n"
        "충분하다면 next_agent를 summary로 지정하세요.\n"
        "재분석 요청 시 reason에 부족한 근거를 구체적으로 작성하세요.\n"
        "시장 데이터가 없으면 숫자를 만들어 내지 마세요.\n"
        "매수나 매도를 실행하지 마세요.\n"
        'JSON 형식: {"next_agent": "macro", "reason": "선택 근거"}\n'
        f"상태:\n{json.dumps(context, ensure_ascii=False, default=str)}"
    )
    for retry in range(MAX_API_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=SUPERVISOR_MODEL,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0},
            )
            decision = json.loads(response.text)
            if not isinstance(decision, dict):
                raise ValueError("Supervisor 응답이 JSON 객체가 아닙니다.")
            return decision
        except Exception as error:
            status = getattr(error, "code", None)
            if status is None:
                status = getattr(error, "status_code", None)
            try:
                status = int(status)
            except (TypeError, ValueError):
                status = None
            if status not in (429, 500, 502, 503, 504) or retry >= MAX_API_RETRIES:
                raise
            print(f"[WARNING] Supervisor API {status}, {retry + 1}/{MAX_API_RETRIES}회 재시도")
            time.sleep(RETRY_DELAY_SECONDS * (retry + 1))
    raise RuntimeError("Supervisor 재시도 한도 초과")


def choose_next_agent(
    state: GraphState,
    available: list[str],
    pending: list[str],
    issues: dict[str, str],
) -> tuple[str, str, str]:
    if pending:
        fallback = pending[0]
    elif issues:
        fallback = next((agent for agent in AGENTS if agent in issues and agent in available), "summary")
    else:
        fallback = "summary"
    allowed = pending if pending else available + ["summary"]
    context = {
        "news_count": len(state.get("news_data", [])),
        "market_count": len(state.get("market_data", [])),
        "analyses": {
            agent: str(state.get(f"{agent}_analysis", ""))[:2000]
            for agent in AGENTS
        },
        "agent_attempts": state.get("agent_attempts", {}),
        "agent_status": state.get("agent_status", {}),
        "available_agents": available,
        "pending_agents": pending,
        "quality_issues": issues,
        "allowed_decisions": allowed,
    }
    try:
        decision = call_supervisor_llm(context)
        selected = decision.get("next_agent")
        reason = decision.get("reason", "")
        if selected not in allowed:
            raise ValueError(f"허용되지 않은 Agent 선택: {selected}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Supervisor 선택 이유가 비어 있습니다.")
        return selected, reason[:500], "llm"
    except Exception as error:
        print(f"[WARNING] Supervisor 판단 실패: {error}")
        return fallback, f"Fallback 실행: {type(error).__name__}", "fallback"


def supervisor_node(state: GraphState) -> dict:
    available = get_available_agents(state)
    pending = get_pending_agents(state)
    issues = get_quality_issues(state)
    retryable_issues = {agent: message for agent, message in issues.items() if agent in available}

    if not available:
        selected, reason, source = "summary", "모든 Agent의 실행 한도 도달", "system"
    elif pending:
        selected, reason, source = pending[0], "필수 Agent 순차 실행", "system"
    elif retryable_issues:
        selected = next(agent for agent in AGENTS if agent in retryable_issues)
        reason = f"실패/누락 결과 재분석: {retryable_issues[selected]}"
        source = "system"
    elif state.get("supervisor_llm_disabled", False):
        selected, reason, source = "summary", "이번 실행의 Supervisor LLM 장애로 품질 평가 생략", "fallback"
    else:
        selected, reason, source = choose_next_agent(state, available, pending, issues)

    attempts = dict(state.get("agent_attempts", {}))
    if selected in AGENTS:
        attempts[selected] = attempts.get(selected, 0) + 1
    log = list(state.get("routing_log", []))
    log.append({
        "agent": selected,
        "reason": reason,
        "source": source,
        "attempt": attempts.get(selected, 0),
    })
    feedback = dict(issues)
    if selected in AGENTS and selected not in feedback and attempts[selected] > 1:
        feedback[selected] = reason
    return {
        "next_agent": selected,
        "supervisor_reason": reason,
        "decision_source": source,
        "agent_attempts": attempts,
        "routing_log": log,
        "quality_feedback": feedback,
        "supervisor_llm_disabled": state.get("supervisor_llm_disabled", False) or source == "fallback",
    }
