from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.agents.macro_agent import analyze_macro
from app.agents.sector_agent import analyze_sector
from app.agents.summary_agent import create_final_summary


class GraphState(TypedDict):
    news_data: list
    market_data: list

    macro_analysis: str
    sector_analysis: str

    final_summary: str


def macro_node(state: GraphState):
    result = analyze_macro(
        state["news_data"]
    )

    return {
        "macro_analysis": result
    }


def sector_node(state: GraphState):
    result = analyze_sector(
        state["market_data"]
    )

    return {
        "sector_analysis": result
    }


def summary_node(state: GraphState):
    result = create_final_summary(
        state["macro_analysis"],
        state["sector_analysis"]
    )

    return {
        "final_summary": result
    }


graph = StateGraph(GraphState)

graph.add_node("macro", macro_node)
graph.add_node("sector", sector_node)
graph.add_node("summary", summary_node)

graph.set_entry_point("macro")

graph.add_edge("macro", "sector")
graph.add_edge("sector", "summary")
graph.add_edge("summary", END)

briefing_graph = graph.compile()