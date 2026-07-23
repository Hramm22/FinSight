from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents.interest_agent import analyze_market_interest
from app.agents.macro_agent import analyze_macro
from app.agents.sector_agent import analyze_sector
from app.agents.summary_agent import create_final_summary
from app.collectors.market_interest_collector import (
    get_market_interest_candidates,
)


class GraphState(TypedDict):
    news_data: list
    market_data: list

    interest_candidates: list

    macro_analysis: str
    sector_analysis: str
    interest_analysis: str

    final_summary: str


def macro_node(state: GraphState):
    return {
        "macro_analysis": analyze_macro(
            state["news_data"]
        )
    }


def sector_node(state: GraphState):
    return {
        "sector_analysis": analyze_sector(
            state["market_data"]
        )
    }


def interest_node(state: GraphState):
    candidates = get_market_interest_candidates(
        state["news_data"]
    )

    return {
        "interest_candidates": candidates,
        "interest_analysis": analyze_market_interest(
            candidates
        ),
    }


def summary_node(state: GraphState):
    return {
        "final_summary": create_final_summary(
            state["macro_analysis"],
            state["sector_analysis"],
            state["interest_analysis"],
        )
    }


graph = StateGraph(GraphState)

graph.add_node("macro", macro_node)
graph.add_node("sector", sector_node)
graph.add_node("interest", interest_node)
graph.add_node("summary", summary_node)

graph.set_entry_point("macro")

graph.add_edge("macro", "sector")
graph.add_edge("sector", "interest")
graph.add_edge("interest", "summary")
graph.add_edge("summary", END)

briefing_graph = graph.compile()