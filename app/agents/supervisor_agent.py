import json
import os
from typing import TypedDict

from dotenv import load_dotenv
from google.genai import types

from app.utils.gemini_client import GeminiPolicy, generate_content

load_dotenv()

AGENTS = ("macro", "sector", "interest")
MAX_ATTEMPTS = 2

SUPERVISOR_MODEL = os.getenv(
    "FINSIGHT_SUPERVISOR_MODEL",
    "gemini-3.1-flash-lite",
)

SUPERVISOR_POLICY = GeminiPolicy(
    timeout_ms=15000,
    max_retries=1,
    retry_delay_seconds=1.0,
)


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
    return [
        agent for agent in AGENTS
        if attempts.get(agent, 0) < MAX_ATTEMPTS
    ]


def get_pending_agents(state: GraphState) -> list[str]:
    attempts = state.get("agent_attempts", {})
    return [
        agent for agent in AGENTS
        if attempts.get(agent, 0) == 0
    ]


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
            detail = errors.get(
                agent,
                "원인을 확인할 수 없습니다.",
            )
            issues[agent] = (
                f"Agent 실행 상태: {status}. 원인: {detail}"
            )

        elif not isinstance(analysis, str) or not analysis.strip():
            issues[agent] = "분석 결과가 비어 있습니다."

    return issues


def call_supervisor_llm(context: dict) -> dict:
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

    response = generate_content(
        agent_name="Supervisor",
        model=SUPERVISOR_MODEL,
        prompt=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
        policy=SUPERVISOR_POLICY,
    )

    raw_result = (response.text or "").strip()

    if not raw_result:
        raise ValueError("Supervisor 응답이 비어 있습니다.")

    decision = json.loads(raw_result)

    if not isinstance(decision, dict):
        raise ValueError("Supervisor 응답이 JSON 객체가 아닙니다.")

    return decision


def choose_next_agent(
    state: GraphState,
    available: list[str],
    pending: list[str],
    issues: dict[str, str],
) -> tuple[str, str, str]:

    if pending:
        fallback = pending[0]
    elif issues:
        fallback = next(
            (
                agent for agent in AGENTS
                if agent in issues and agent in available
            ),
            "summary",
        )
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
        return (
            fallback,
            f"Fallback 실행: {type(error).__name__}",
            "fallback",
        )


def supervisor_node(state: GraphState) -> dict:
    available = get_available_agents(state)
    pending = get_pending_agents(state)
    issues = get_quality_issues(state)

    retryable_issues = {
        agent: message
        for agent, message in issues.items()
        if agent in available
    }

    if not available:
        selected = "summary"
        reason = "모든 Agent의 실행 한도 도달"
        source = "system"

    elif pending:
        selected = pending[0]
        reason = "필수 Agent 순차 실행"
        source = "system"

    elif retryable_issues:
        selected = next(
            agent for agent in AGENTS
            if agent in retryable_issues
        )
        reason = f"실패/누락 결과 재분석: {retryable_issues[selected]}"
        source = "system"

    elif state.get("supervisor_llm_disabled", False):
        selected = "summary"
        reason = "이번 실행의 Supervisor LLM 장애로 품질 평가 생략"
        source = "fallback"

    else:
        selected, reason, source = choose_next_agent(
            state,
            available,
            pending,
            issues,
        )

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

    if (
        selected in AGENTS
        and selected not in feedback
        and attempts[selected] > 1
    ):
        feedback[selected] = reason

    return {
        "next_agent": selected,
        "supervisor_reason": reason,
        "decision_source": source,
        "agent_attempts": attempts,
        "routing_log": log,
        "quality_feedback": feedback,
        "supervisor_llm_disabled": (
            state.get("supervisor_llm_disabled", False)
            or source == "fallback"
        ),
    }