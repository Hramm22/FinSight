import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import SessionLocal
from app.db.models import Briefing
from app.graph.briefing_graph import briefing_graph
from app.services.briefing_service import create_briefing_data


router = APIRouter(
    prefix="/briefings",
    tags=["Briefings"],
)


def parse_json_field(value: str | None) -> Any:
    """
    DB에 문자열 형태로 저장된 JSON 데이터를
    Python 객체로 변환합니다.
    """
    if not value:
        return []

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_briefing(briefing: Briefing) -> dict:
    """
    DB Briefing 객체를 API 응답 형식으로 변환합니다.
    """
    return {
        "id": briefing.id,
        "created_at": briefing.created_at,
        "market_data": parse_json_field(briefing.market_data),
        "news_data": parse_json_field(briefing.news_data),
        "macro_analysis": briefing.macro_analysis,
        "sector_analysis": briefing.sector_analysis,
        "interest_analysis": briefing.interest_analysis,
        "ai_summary": briefing.ai_summary,
    }


def generate_briefing_result() -> dict:
    """
    뉴스와 시장 데이터를 수집하고 LangGraph를 실행합니다.
    """
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
        "macro_analysis": graph_result.get("macro_analysis", ""),
        "sector_analysis": graph_result.get("sector_analysis", ""),
        "interest_analysis": graph_result.get("interest_analysis", ""),
        "final_summary": graph_result.get("final_summary", ""),
    }


def save_briefing(result: dict) -> Briefing:
    """
    생성된 브리핑 결과를 DB에 저장합니다.
    """
    db = SessionLocal()

    try:
        briefing = Briefing(
            market_data=json.dumps(
                result["market_data"],
                ensure_ascii=False,
                default=str,
            ),
            news_data=json.dumps(
                result["news_data"],
                ensure_ascii=False,
                default=str,
            ),
            macro_analysis=result["macro_analysis"],
            sector_analysis=result["sector_analysis"],
            interest_analysis=result["interest_analysis"],
            ai_summary=result["final_summary"],
        )

        db.add(briefing)
        db.commit()
        db.refresh(briefing)

        return briefing

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"브리핑 저장 중 오류가 발생했습니다: {str(exc)}",
        ) from exc

    finally:
        db.close()


@router.post(
    "/run",
    status_code=status.HTTP_201_CREATED,
    summary="새 브리핑 생성",
    description=(
        "뉴스와 시장 데이터를 수집하고 Multi-Agent 분석을 실행한 뒤 "
        "결과를 데이터베이스에 저장합니다."
    ),
)
def run_briefing():
    try:
        result = generate_briefing_result()
        saved_briefing = save_briefing(result)

        return {
            "message": "브리핑 생성 및 저장이 완료되었습니다.",
            "id": saved_briefing.id,
            "created_at": saved_briefing.created_at,
            "market_data": result["market_data"],
            "news_data": result["news_data"],
            "macro_analysis": result["macro_analysis"],
            "sector_analysis": result["sector_analysis"],
            "interest_analysis": result["interest_analysis"],
            "ai_summary": result["final_summary"],
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"브리핑 생성 중 오류가 발생했습니다: {str(exc)}",
        ) from exc


@router.get(
    "",
    summary="브리핑 히스토리 조회",
    description="저장된 브리핑 목록을 최신순으로 조회합니다.",
)
def get_briefing_history(limit: int = 20):
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit 값은 1 이상이어야 합니다.",
        )

    if limit > 100:
        limit = 100

    db = SessionLocal()

    try:
        briefings = (
            db.query(Briefing)
            .order_by(Briefing.id.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": briefing.id,
                "created_at": briefing.created_at,
            }
            for briefing in briefings
        ]

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"브리핑 목록 조회 중 오류가 발생했습니다: {str(exc)}",
        ) from exc

    finally:
        db.close()


@router.get(
    "/latest",
    summary="최신 브리핑 조회",
    description="가장 최근에 저장된 브리핑을 조회합니다.",
)
def get_latest_briefing():
    db = SessionLocal()

    try:
        briefing = (
            db.query(Briefing)
            .order_by(Briefing.id.desc())
            .first()
        )

        if not briefing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="저장된 브리핑이 없습니다.",
            )

        return serialize_briefing(briefing)

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"최신 브리핑 조회 중 오류가 발생했습니다: {str(exc)}",
        ) from exc

    finally:
        db.close()


@router.get(
    "/{briefing_id}",
    summary="브리핑 상세 조회",
    description="브리핑 ID를 기준으로 저장된 상세 결과를 조회합니다.",
)
def get_briefing_by_id(briefing_id: int):
    db = SessionLocal()

    try:
        briefing = (
            db.query(Briefing)
            .filter(Briefing.id == briefing_id)
            .first()
        )

        if not briefing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="브리핑을 찾을 수 없습니다.",
            )

        return serialize_briefing(briefing)

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"브리핑 조회 중 오류가 발생했습니다: {str(exc)}",
        ) from exc

    finally:
        db.close()