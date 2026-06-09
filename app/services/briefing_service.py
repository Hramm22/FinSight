import json

from app.collectors.market_collector import get_watchlist_summaries
from app.collectors.news_collector import get_all_news
from app.db.database import Base, SessionLocal, engine
from app.db.models import Briefing
from app.graph.briefing_graph import briefing_graph


Base.metadata.create_all(bind=engine)


def create_briefing_data() -> dict:
    market_data = get_watchlist_summaries()
    news_data = get_all_news()

    return {
        "market_data": market_data,
        "news_data": news_data,
    }


def save_briefing(
    briefing_data: dict,
    graph_result: dict,
) -> Briefing:
    db = SessionLocal()

    briefing = Briefing(
        market_data=json.dumps(
            briefing_data["market_data"],
            ensure_ascii=False,
        ),
        news_data=json.dumps(
            briefing_data["news_data"],
            ensure_ascii=False,
        ),
        macro_analysis=graph_result["macro_analysis"],
        sector_analysis=graph_result["sector_analysis"],
        ai_summary=graph_result["final_summary"],
    )

    db.add(briefing)
    db.commit()
    db.refresh(briefing)
    db.close()

    return briefing


def format_briefing_data(briefing_data: dict) -> str:
    output = []

    output.append("=" * 60)
    output.append("FinSight 브리핑 데이터")
    output.append("=" * 60)

    output.append("\n[시장 데이터]")

    for stock in briefing_data["market_data"]:
        output.append(
            f"- {stock['name']}({stock['ticker']}): "
            f"현재가 {stock['current_price']:,}원 / "
            f"1개월 {stock['month_return']}% / "
            f"3개월 {stock['three_month_return']}% / "
            f"1년 {stock['year_return']}%"
        )

    output.append("\n[뉴스 데이터]")

    for news in briefing_data["news_data"]:
        output.append(
            f"- [{news['source']}] {news['title']}\n"
            f"  {news['link']}"
        )

    return "\n".join(output)


if __name__ == "__main__":
    briefing_data = create_briefing_data()

    print(format_briefing_data(briefing_data))

    print("\n" + "=" * 60)
    print("LangGraph 실행")
    print("=" * 60)

    result = briefing_graph.invoke(
        {
            "news_data": briefing_data["news_data"],
            "market_data": briefing_data["market_data"],
        }
    )

    saved_briefing = save_briefing(
        briefing_data,
        result,
    )

    print("\n" + "=" * 60)
    print("AI 시장 브리핑")
    print("=" * 60)

    print(result["final_summary"])

    print("\n" + "=" * 60)
    print("DB 저장 완료")
    print("=" * 60)
    print(f"저장된 브리핑 ID: {saved_briefing.id}")