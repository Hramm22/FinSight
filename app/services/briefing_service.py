from app.collectors.market_collector import get_watchlist_summaries
from app.collectors.news_collector import get_all_news


def create_briefing_data() -> dict:
    market_data = get_watchlist_summaries()
    news_data = get_all_news()

    return {
        "market_data": market_data,
        "news_data": news_data,
    }


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
            f"- [{news['source']}] {news['title']}\n  {news['link']}"
        )

    return "\n".join(output)


if __name__ == "__main__":
    briefing_data = create_briefing_data()
    print(format_briefing_data(briefing_data))