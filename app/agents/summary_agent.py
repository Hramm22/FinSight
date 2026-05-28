def create_summary(briefing_data: dict) -> str:
    market_data = briefing_data["market_data"]
    news_data = briefing_data["news_data"]

    strongest_stock = max(market_data, key=lambda stock: stock["month_return"])
    weakest_stock = min(market_data, key=lambda stock: stock["month_return"])

    recent_news_titles = [news["title"] for news in news_data[:5]]

    summary = f"""
[FinSight AI 시장 브리핑]

최근 1개월 기준 가장 강한 흐름을 보인 종목은 {strongest_stock['name']}입니다.
{strongest_stock['name']}의 최근 1개월 수익률은 {strongest_stock['month_return']}%입니다.

반면 최근 1개월 기준 가장 약한 흐름을 보인 종목은 {weakest_stock['name']}입니다.
{weakest_stock['name']}의 최근 1개월 수익률은 {weakest_stock['month_return']}%입니다.

오늘 수집된 주요 경제/산업 뉴스는 다음과 같습니다.

- {recent_news_titles[0]}
- {recent_news_titles[1]}
- {recent_news_titles[2]}

현재 시장 데이터와 뉴스 흐름을 종합하면,
강한 상승 흐름을 보이는 종목과 단기 약세 종목이 뚜렷하게 나뉘고 있어
사용자는 뉴스 이슈와 최근 수익률 흐름을 함께 참고할 필요가 있습니다.

※ 본 브리핑은 투자 참고용 정보이며, 최종 투자 판단은 사용자에게 있습니다.
""".strip()

    return summary