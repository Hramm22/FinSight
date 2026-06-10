import json

from fastapi import APIRouter, HTTPException

from app.db.database import SessionLocal
from app.db.models import Briefing
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


@router.get("/briefing/history")
def get_briefing_history():
    db = SessionLocal()

    briefings = (
        db.query(Briefing)
        .order_by(Briefing.id.desc())
        .all()
    )

    db.close()

    return [
        {
            "id": briefing.id,
            "created_at": briefing.created_at,
        }
        for briefing in briefings
    ]


@router.get("/briefing/{briefing_id}")
def get_briefing_by_id(briefing_id: int):
    db = SessionLocal()

    briefing = (
        db.query(Briefing)
        .filter(Briefing.id == briefing_id)
        .first()
    )

    db.close()

    if not briefing:
        raise HTTPException(
            status_code=404,
            detail="브리핑을 찾을 수 없습니다.",
        )

    return {
        "id": briefing.id,
        "created_at": briefing.created_at,
        "market_data": json.loads(briefing.market_data),
        "news_data": json.loads(briefing.news_data),
        "macro_analysis": briefing.macro_analysis,
        "sector_analysis": briefing.sector_analysis,
        "ai_summary": briefing.ai_summary,
    }