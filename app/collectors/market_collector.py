from datetime import datetime, timedelta

from pykrx import stock


BASE_WATCHLIST = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "005380": "현대차",
    "035720": "카카오",
}


STOCK_NAME_TO_TICKER = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "NAVER": "035420",
    "네이버": "035420",
    "현대차": "005380",
    "현대자동차": "005380",
    "기아": "000270",
    "카카오": "035720",
    "카카오페이": "377300",
    "삼성물산": "028260",
    "삼성전기": "009150",
    "LG전자": "066570",
    "LG유플러스": "032640",
    "LGU+": "032640",
    "LG에너지솔루션": "373220",
    "삼성SDI": "006400",
    "삼성바이오로직스": "207940",
    "셀트리온": "068270",
    "두산에너빌리티": "034020",
    "한화에어로스페이스": "012450",
    "한화에어로": "012450",
    "한국항공우주": "047810",
    "HD현대중공업": "329180",
    "현대중공업": "329180",
    "POSCO홀딩스": "005490",
    "포스코홀딩스": "005490",
    "포스코": "005490",
    "대우건설": "047040",
    "HMM": "011200",
}


def extract_tickers_from_news(news_data: list[dict]) -> dict[str, str]:
    extracted = {}

    for news in news_data:
        title = news["title"]

        for stock_name, ticker in STOCK_NAME_TO_TICKER.items():
            if stock_name in title:
                official_name = stock.get_market_ticker_name(ticker)
                extracted[ticker] = official_name

    return extracted


def build_dynamic_watchlist(
    news_data: list[dict] | None = None,
    extra_tickers: dict[str, str] | None = None,
    max_count: int = 10,
) -> dict[str, str]:
    watchlist = BASE_WATCHLIST.copy()

    if news_data:
        news_tickers = extract_tickers_from_news(news_data)
        watchlist.update(news_tickers)

    if extra_tickers:
        watchlist.update(extra_tickers)

    return dict(list(watchlist.items())[:max_count])


def get_stock_summary(ticker: str) -> dict:
    today = datetime.today()

    recent_start = today - timedelta(days=10)
    one_month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    one_year_ago = today - timedelta(days=365)

    current_data = stock.get_market_ohlcv_by_date(
        recent_start.strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
        ticker,
    )

    month_data = stock.get_market_ohlcv_by_date(
        one_month_ago.strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
        ticker,
    )

    three_month_data = stock.get_market_ohlcv_by_date(
        three_months_ago.strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
        ticker,
    )

    year_data = stock.get_market_ohlcv_by_date(
        one_year_ago.strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
        ticker,
    )

    if current_data.empty:
        raise ValueError(f"{ticker} 최근 거래 데이터를 가져오지 못했습니다.")

    if month_data.empty or three_month_data.empty or year_data.empty:
        raise ValueError(f"{ticker} 기간별 주가 데이터를 가져오지 못했습니다.")

    current_price = current_data["종가"].iloc[-1]

    month_return = (
        (month_data["종가"].iloc[-1] / month_data["종가"].iloc[0]) - 1
    ) * 100

    three_month_return = (
        (three_month_data["종가"].iloc[-1] / three_month_data["종가"].iloc[0]) - 1
    ) * 100

    year_return = (
        (year_data["종가"].iloc[-1] / year_data["종가"].iloc[0]) - 1
    ) * 100

    return {
        "ticker": ticker,
        "name": stock.get_market_ticker_name(ticker),
        "current_price": int(current_price),
        "month_return": float(round(month_return, 2)),
        "three_month_return": float(round(three_month_return, 2)),
        "year_return": float(round(year_return, 2)),
    }


def get_watchlist_summaries(
    news_data: list[dict] | None = None,
    extra_tickers: dict[str, str] | None = None,
    max_count: int = 10,
) -> list[dict]:
    summaries = []

    watchlist = build_dynamic_watchlist(
        news_data=news_data,
        extra_tickers=extra_tickers,
        max_count=max_count,
    )

    for ticker in watchlist.keys():
        try:
            summary = get_stock_summary(ticker)
            summaries.append(summary)

        except Exception as error:
            print(f"[WARNING] {ticker} 시장 데이터 수집 실패: {error}")

    return summaries


def format_stock_summary(summary: dict) -> str:
    return f"""
[{summary['name']} ({summary['ticker']}) 시장 데이터 요약]

현재가: {summary['current_price']:,}원
최근 1개월 수익률: {summary['month_return']}%
최근 3개월 수익률: {summary['three_month_return']}%
최근 1년 수익률: {summary['year_return']}%
""".strip()


if __name__ == "__main__":
    results = get_watchlist_summaries()

    for result in results:
        print(format_stock_summary(result))
        print("-" * 40)