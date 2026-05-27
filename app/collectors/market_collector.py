from datetime import datetime, timedelta

from pykrx import stock


WATCHLIST = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "005380": "현대차",
    "035720": "카카오",
}


def get_stock_summary(ticker: str) -> dict:
    today = datetime.today()
    yesterday = today - timedelta(days=1)

    one_month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    one_year_ago = today - timedelta(days=365)

    current_data = stock.get_market_ohlcv_by_date(
        yesterday.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d"),
        ticker,
    )

    month_data = stock.get_market_ohlcv_by_date(
        one_month_ago.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d"),
        ticker,
    )

    three_month_data = stock.get_market_ohlcv_by_date(
        three_months_ago.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d"),
        ticker,
    )

    year_data = stock.get_market_ohlcv_by_date(
        one_year_ago.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d"),
        ticker,
    )

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
        "current_price": int(current_data["종가"].iloc[-1]),
        "month_return": float(round(month_return, 2)),
        "three_month_return": float(round(three_month_return, 2)),
        "year_return": float(round(year_return, 2)),
    }


def get_watchlist_summaries() -> list[dict]:
    summaries = []

    for ticker in WATCHLIST.keys():
        summary = get_stock_summary(ticker)
        summaries.append(summary)

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