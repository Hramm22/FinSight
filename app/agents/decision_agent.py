import json
import math
import os
import re
from typing import Any

ACTIONS = {"HOLD", "RESEARCH", "PROPOSE_TRADE", "NO_ACTION"}
TREND_ORDER = ("강세", "긍정 관찰", "중립", "주의 관찰", "약세")
REQUIRED_AGENTS = ("macro", "sector", "interest")


def no_action(reason: str) -> dict:
    return {"action": "NO_ACTION", "reason": reason, "ticker": "", "side": "", "evidence": []}


def _valid_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _verified_stocks(state: dict) -> list[dict]:
    market = state.get("market_data") or []
    sector = state.get("sector_data") or {}
    groups = sector.get("groups") if isinstance(sector, dict) else None
    if not isinstance(groups, dict):
        return []

    by_ticker = {}
    for stock in market:
        if not isinstance(stock, dict):
            continue
        ticker = str(stock.get("ticker") or "").strip()
        if not ticker:
            continue
        if ticker in by_ticker:
            return []
        if not all(_valid_number(stock.get(key)) for key in ("month_return", "three_month_return", "year_return")):
            continue
        by_ticker[ticker] = stock

    verified = []
    seen = set()
    for trend in TREND_ORDER:
        entries = groups.get(trend, [])
        if not isinstance(entries, list):
            return []
        for item in entries:
            if not isinstance(item, dict):
                return []
            ticker = str(item.get("ticker") or "").strip()
            source = by_ticker.get(ticker)
            if not source or ticker in seen:
                return []
            score = round(source["month_return"] * 0.5 + source["three_month_return"] * 0.3 + source["year_return"] * 0.2, 2)
            month = source["month_return"]
            three_month = source["three_month_return"]
            expected = ("강세" if score >= 30 and month >= 0 else
                        "긍정 관찰" if score >= 10 else
                        "약세" if score <= -20 else
                        "주의 관찰" if month <= -10 or three_month <= -10 else "중립")
            if trend != expected:
                return []
            if any(item.get(key) != source.get(key) for key in ("month_return", "three_month_return", "year_return")):
                return []
            if not _valid_number(item.get("momentum_score")) or abs(item["momentum_score"] - score) > 0.011:
                return []
            seen.add(ticker)
            verified.append({
                "ticker": ticker,
                "name": str(source.get("name") or ticker),
                "trend": trend,
                "month_return": month,
                "three_month_return": three_month,
                "year_return": source["year_return"],
                "momentum_score": score,
            })
    if set(by_ticker) != seen:
        return []
    return verified


def build_decision_context(state: dict) -> dict:
    market = state.get("market_data") or []
    candidates = state.get("interest_candidates") or []
    stocks = []
    for item in market:
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "").strip()
        if ticker:
            stocks.append({key: item.get(key) for key in (
                "ticker", "name", "current_price", "month_return", "three_month_return", "year_return"
            )})
    interests = []
    for item in candidates:
        if isinstance(item, dict):
            interests.append({key: item.get(key) for key in (
                "ticker", "name", "news_count", "change_rate", "interest_score"
            )})
    return {
        "agent_status": state.get("agent_status") or {},
        "macro_analysis": str(state.get("macro_analysis") or "")[:3000],
        "sector_analysis": str(state.get("sector_analysis") or "")[:3000],
        "interest_analysis": str(state.get("interest_analysis") or "")[:3000],
        "stocks": stocks[:30],
        "interests": interests[:30],
        "verified_stocks": _verified_stocks(state)[:30],
    }


def parse_decision(raw: str, context: dict) -> dict:
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
        data = json.loads(cleaned)
    except (ValueError, TypeError, AttributeError):
        return no_action("LLM 응답이 유효한 JSON이 아닙니다.")
    if not isinstance(data, dict) or data.get("action") not in ACTIONS:
        return no_action("허용되지 않은 행동입니다.")
    action = data["action"]
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return no_action("판단 근거가 없습니다.")
    ticker = str(data.get("ticker") or "").strip()
    side = str(data.get("side") or "").upper().strip()
    evidence = data.get("evidence")
    if action != "PROPOSE_TRADE" and evidence is None:
        evidence = []
    if not isinstance(evidence, list) or any(not isinstance(x, str) for x in evidence):
        return no_action("근거 목록 형식이 잘못되었습니다.")
    if action == "PROPOSE_TRADE":
        allowed = {str(x["ticker"]) for x in context["stocks"]}
        if ticker not in allowed or side not in {"BUY", "SELL"} or not evidence:
            return no_action("주문 제안의 종목, 방향 또는 근거가 유효하지 않습니다.")
    else:
        ticker, side = "", ""
    return {"action": action, "reason": reason.strip()[:1000],
            "ticker": ticker, "side": side, "evidence": evidence[:5]}


def _fact(stock: dict) -> str:
    return (f"{stock['name']}({stock['ticker']}): {stock['trend']}, "
            f"1개월 {stock['month_return']}%, 3개월 {stock['three_month_return']}%, "
            f"1년 {stock['year_return']}%, 모멘텀 점수 {stock['momentum_score']}")


def validate_decision(decision: dict, context: dict) -> dict:
    if decision["action"] == "NO_ACTION":
        return decision
    stocks = context.get("verified_stocks") or []
    if not stocks:
        return no_action("시장 수익률과 Sector 분류를 교차 검증할 수 없습니다.")
    facts = [_fact(stock) for stock in stocks]
    if decision["action"] == "PROPOSE_TRADE":
        matched = next((stock for stock in stocks if stock["ticker"] == decision["ticker"]), None)
        if matched is None:
            return no_action("거래 제안 종목의 분석 데이터가 검증되지 않았습니다.")
        # Exact matching is intentional: free-form LLM evidence is not independently verified.
        canonical = _fact(matched)
        if not decision["evidence"] or any(item != canonical for item in decision["evidence"]):
            return no_action("거래 제안 근거가 검증된 종목 데이터와 일치하지 않습니다.")
        return {**decision, "reason": f"검증된 데이터 기반 제안: {canonical}", "evidence": [canonical]}
    if decision["action"] == "RESEARCH":
        return {**decision, "reason": "기존 수집 데이터의 추가 확인이 필요합니다. " + "; ".join(facts[:5]), "evidence": []}
    return {**decision, "reason": "검증된 시장 데이터 기준 관찰 유지: " + "; ".join(facts[:5]), "evidence": []}


def call_decision_llm(context: dict) -> str:
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 없습니다.")
    client = genai.Client(api_key=api_key)
    prompt = (
        "당신은 FinSight Decision Agent입니다. 입력 자료에 없는 사실을 만들지 마세요. "
        "투자 확신이 부족하면 HOLD 또는 NO_ACTION을 선택하세요. "
        "RESEARCH는 기존 자료 재검토를 의미합니다. "
        "PROPOSE_TRADE는 주문 실행이 아닌 승인 전 제안입니다. "
        "반드시 JSON 객체만 반환하세요. 키: action, reason, ticker, side, evidence. "
        "action은 HOLD, RESEARCH, PROPOSE_TRADE, NO_ACTION 중 하나. "
        "반환 JSON 예시: {\"action\":\"HOLD\",\"reason\":\"관찰 필요\",\"ticker\":\"\",\"side\":\"\",\"evidence\":[]}. "
        "evidence는 반드시 문자열 배열입니다. HOLD, RESEARCH, NO_ACTION에서는 빈 배열 []을 사용하세요. "
        "PROPOSE_TRADE라면 verified_stocks의 해당 종목을 선택하고 evidence에 해당 종목의 "
        "'종목명(티커): 분류, 1개월 X%, 3개월 Y%, 1년 Z%, 모멘텀 점수 S' 형식의 사실 문장을 정확히 한 개 넣으세요. "
        "주문 수량, 금액, 체결을 생성하지 마세요.\n"
        + json.dumps(context, ensure_ascii=False, default=str)
    )
    response = client.models.generate_content(
        model=os.getenv("DECISION_GEMINI_MODEL", "gemini-3.1-flash-lite"),
        contents=prompt,
    )
    return (response.text or "").strip()


def make_decision(state: dict) -> dict:
    context = build_decision_context(state)
    statuses = context["agent_status"]
    if any(statuses.get(agent) != "success" for agent in REQUIRED_AGENTS):
        return no_action("필수 Agent 중 정상 완료되지 않은 분석이 있습니다.")
    sector_present = "sector_data" in state and state["sector_data"] is not None
    if sector_present and not context["verified_stocks"]:
        return no_action("시장 수익률과 Sector 분류를 교차 검증할 수 없습니다.")
    try:
        decision = parse_decision(call_decision_llm(context), context)
        if not context["verified_stocks"]:
            if decision["action"] in {"HOLD", "RESEARCH"}:
                return {**decision, "reason": "검증된 Sector 데이터가 없어 판단 근거를 확인할 수 없습니다. 관찰 또는 추가 확인이 필요합니다.", "evidence": []}
            if decision["action"] == "PROPOSE_TRADE":
                return no_action("Sector 검증 데이터가 없어 거래를 제안할 수 없습니다.")
            return decision
        return validate_decision(decision, context)
    except Exception as exc:
        return no_action(f"Decision Agent 호출 실패: {type(exc).__name__}")
