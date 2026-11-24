from langgraph.graph import END, StateGraph

from app.agents.decision_agent import make_decision
from app.agents.interest_agent import analyze_market_interest
from app.agents.macro_agent import analyze_macro_with_status
from app.agents.sector_agent import analyze_sector, build_sector_json
from app.agents.summary_agent import create_final_summary
from app.agents.supervisor_agent import GraphState, supervisor_node
from app.collectors.market_interest_collector import get_market_interest_candidates


class DecisionGraphState(GraphState, total=False):
    sector_data: dict
    decision: dict
    research_result: dict
    trade_proposal: dict


def route_from_supervisor(state: DecisionGraphState) -> str:
    return state["next_agent"]


def macro_node(state: DecisionGraphState) -> dict:
    result = analyze_macro_with_status(
        state.get("news_data", []),
        feedback=state.get("quality_feedback", {}).get("macro", ""),
    )
    statuses = dict(state.get("agent_status", {}))
    errors = dict(state.get("agent_errors", {}))
    statuses["macro"] = result["status"]
    errors["macro"] = result["error"]
    return {"macro_analysis": result["analysis"], "agent_status": statuses, "agent_errors": errors}


def sector_node(state: DecisionGraphState) -> dict:
    market_data = state.get("market_data", [])
    analysis = analyze_sector(market_data)
    statuses = dict(state.get("agent_status", {}))
    statuses["sector"] = "success" if isinstance(analysis, str) and analysis.strip() else "error"
    errors = dict(state.get("agent_errors", {}))
    errors["sector"] = "" if statuses["sector"] == "success" else "분석 결과가 비어 있습니다."
    return {
        "sector_analysis": analysis,
        "sector_data": build_sector_json(market_data),
        "agent_status": statuses,
        "agent_errors": errors,
    }


def interest_node(state: DecisionGraphState) -> dict:
    candidates = get_market_interest_candidates(state.get("news_data", []))
    analysis = analyze_market_interest(candidates)
    statuses = dict(state.get("agent_status", {}))
    statuses["interest"] = "success" if isinstance(analysis, str) and analysis.strip() else "error"
    errors = dict(state.get("agent_errors", {}))
    errors["interest"] = "" if statuses["interest"] == "success" else "분석 결과가 비어 있습니다."
    return {
        "interest_candidates": candidates,
        "interest_analysis": analysis,
        "agent_status": statuses,
        "agent_errors": errors,
    }


def decision_node(state: DecisionGraphState) -> dict:
    return {"decision": make_decision(state)}


def route_from_decision(state: DecisionGraphState) -> str:
    action = state["decision"]["action"]
    if action == "RESEARCH":
        return "research"
    if action == "PROPOSE_TRADE":
        return "proposal"
    return "summary"


def research_node(state: DecisionGraphState) -> dict:
    return {"research_result": {
        "status": "reviewed",
        "note": "기존 수집 데이터의 존재 여부만 재확인했습니다. 신규 외부 조사는 수행하지 않았습니다.",
        "news_count": len(state.get("news_data") or []),
        "market_count": len(state.get("market_data") or []),
        "interest_count": len(state.get("interest_candidates") or []),
    }}


def proposal_node(state: DecisionGraphState) -> dict:
    decision = state["decision"]
    ticker = decision["ticker"]
    matches = [x for x in state.get("market_data", []) if str(x.get("ticker")) == ticker]
    if len(matches) != 1:
        return {"trade_proposal": {"status": "rejected", "reason": "종목 데이터 검증 실패"}}
    return {"trade_proposal": {
        "status": "awaiting_approval", "ticker": ticker, "side": decision["side"],
        "reason": decision["reason"], "evidence": decision["evidence"],
        "quantity": None, "executed": False,
        "note": "제안 기록만 생성했습니다. 승인·주문 실행 기능은 연결되지 않았습니다.",
    }}


def summary_node(state: DecisionGraphState) -> dict:
    return {"final_summary": create_final_summary(
        state.get("macro_analysis", ""),
        state.get("sector_analysis", ""),
        state.get("interest_analysis", ""),
        decision=state.get("decision"),
        research_result=state.get("research_result"),
        trade_proposal=state.get("trade_proposal"),
    )}


graph = StateGraph(DecisionGraphState)
for name, node in (
    ("supervisor", supervisor_node), ("macro", macro_node),
    ("sector", sector_node), ("interest", interest_node),
    ("decision", decision_node), ("research", research_node),
    ("proposal", proposal_node), ("summary", summary_node),
):
    graph.add_node(name, node)
graph.set_entry_point("supervisor")
graph.add_conditional_edges("supervisor", route_from_supervisor,
    {"macro": "macro", "sector": "sector", "interest": "interest", "summary": "decision"})
for name in ("macro", "sector", "interest"):
    graph.add_edge(name, "supervisor")
graph.add_conditional_edges("decision", route_from_decision,
    {"research": "research", "proposal": "proposal", "summary": "summary"})
graph.add_edge("research", "summary")
graph.add_edge("proposal", "summary")
graph.add_edge("summary", END)
briefing_graph = graph.compile()
