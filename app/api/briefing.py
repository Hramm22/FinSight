from fastapi import APIRouter

from app.graph.briefing_graph import briefing_graph
from app.services.briefing_service import create_briefing_data

router = APIRouter()


@router.get("/briefing")
def get_briefing():
    briefing_data = create_briefing_data()

    graph_result = briefing_graph.invoke(
        {
            "news_data": briefing_data["news_data"],
            "market_data": briefing_data["market_data"],
        }
    )

    return {
        "market_data": briefing_data["market_data"],
        "news_data": briefing_data["news_data"],
        "macro_analysis": graph_result["macro_analysis"],
        "sector_analysis": graph_result["sector_analysis"],
        "ai_summary": graph_result["final_summary"],
    }