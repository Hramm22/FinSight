from datetime import date, datetime, timedelta, timezone

from pykrx import stock


BASE_WATCHLIST = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "005380": "현대차",
    "035720": "카카오",
}

STOCK_NAME_TO_TICKER = {
    "삼성전자": "005930", "SK하이닉스": "000660", "NAVER": "035420",
    "네이버": "035420", "현대차": "005380", "현대자동차": "005380",
    "기아": "000270", "카카오": "035720", "카카오페이": "377300",
    "삼성물산": "028260", "삼성전기": "009150", "LG전자": "066570",
    "LG유플러스": "032640", "LGU+": "032640", "LG에너지솔루션": "373220",
    "삼성SDI": "006400", "삼성바이오로직스": "207940", "셀트리온": "068270",
    "두산에너빌리티": "034020", "한화에어로스페이스": "012450",
    "한화에어로": "012450", "한국항공우주": "047810",
    "HD현대중공업": "329180", "현대중공업": "329180",
    "POSCO홀딩스": "005490", "포스코홀딩스": "005490",
    "포스코": "005490", "대우건설": "047040", "HMM": "011200",
}


def parse_as_of_date(as_of_date: str | date | None) -> date:
    if as_of_date is None:
        return date.today()

    if isinstance(as_of_date, datetime):
        raise TypeError(
            "as_of_date에는 날짜만 입력하세요. 예: '2025-06-10'"
        )

    if isinstance(as_of_date, date):
        parsed = as_of_date
    elif isinstance(as_of_date, str):
        try:
            parsed = date.fromisoformat(as_of_date)
        except ValueError as error:
            raise ValueError(
                "as_of_date 형식은 YYYY-MM-DD여야 합니다."
            ) from error
    else:
        raise TypeError(
            "as_of_date는 YYYY-MM-DD 문자열 또는 date 객체여야 합니다."
        )

    if parsed > date.today():
        raise ValueError(
            "미래 날짜는 분석 기준일로 사용할 수 없습니다."
        )

    return parsed


def extract_tickers_from_news(
    news_data: list[dict],
) -> dict[str, str]:
    extracted = {}

    for news in news_data:
        title = news.get("title", "")

        for stock_name, ticker in STOCK_NAME_TO_TICKER.items():
            if stock_name in title:
                extracted[ticker] = (
                    stock.get_market_ticker_name(ticker) or stock_name
                )

    return extracted


def build_dynamic_watchlist(
    news_data: list[dict] | None = None,
    extra_tickers: dict[str, str] | None = None,
    max_count: int = 10,
) -> dict[str, str]:
    if max_count < 1:
        raise ValueError("max_count는 1 이상이어야 합니다.")

    watchlist = BASE_WATCHLIST.copy()

    if news_data:
        watchlist.update(
            extract_tickers_from_news(news_data)
        )

    if extra_tickers:
        watchlist.update(extra_tickers)

    return dict(
        list(watchlist.items())[:max_count]
    )


def _get_close_on_or_before(
    frame,
    cutoff: date,
) -> tuple[date, float]:
    eligible = frame.loc[
        frame.index.date <= cutoff
    ]

    if eligible.empty:
        raise ValueError(
            f"{cutoff} 이전 거래 데이터가 없습니다."
        )

    row_date = eligible.index[-1].date()
    close = float(eligible["종가"].iloc[-1])

    if close <= 0:
        raise ValueError(
            f"{row_date} 종가가 올바르지 않습니다: {close}"
        )

    return row_date, close


def get_stock_summary(
    ticker: str,
    as_of_date: str | date | None = None,
) -> dict:
    requested_date = parse_as_of_date(as_of_date)
    start_date = requested_date - timedelta(days=380)

    frame = stock.get_market_ohlcv_by_date(
        start_date.strftime("%Y%m%d"),
        requested_date.strftime("%Y%m%d"),
        ticker,
    )

    if frame.empty:
        raise ValueError(
            f"{ticker}: 기준일 이전 주가 데이터를 찾지 못했습니다."
        )

    frame = frame.sort_index()

    actual_date, current_price = _get_close_on_or_before(
        frame,
        requested_date,
    )

    def calculate_return(days: int) -> tuple[float, str]:
        target_date = actual_date - timedelta(days=days)

        historical_date, historical_price = (
            _get_close_on_or_before(
                frame,
                target_date,
            )
        )

        percent = (
            current_price / historical_price - 1
        ) * 100

        return round(percent, 2), historical_date.isoformat()

    month_return, month_base_date = calculate_return(30)
    three_month_return, three_month_base_date = (
        calculate_return(90)
    )
    year_return, year_base_date = calculate_return(365)

    return {
        "ticker": ticker,
        "name": stock.get_market_ticker_name(ticker) or ticker,
        "current_price": int(current_price),
        "month_return": month_return,
        "three_month_return": three_month_return,
        "year_return": year_return,
        "as_of_date": requested_date.isoformat(),
        "price_date": actual_date.isoformat(),
        "return_base_dates": {
            "month": month_base_date,
            "three_months": three_month_base_date,
            "year": year_base_date,
        },
    }


def get_watchlist_summaries(
    news_data: list[dict] | None = None,
    extra_tickers: dict[str, str] | None = None,
    max_count: int = 10,
    as_of_date: str | date | None = None,
) -> list[dict]:
    requested_date = parse_as_of_date(as_of_date)

    watchlist = build_dynamic_watchlist(
        news_data=news_data,
        extra_tickers=extra_tickers,
        max_count=max_count,
    )

    summaries = []
    failed_tickers = []

    for ticker, name in watchlist.items():
        try:
            summary = get_stock_summary(
                ticker=ticker,
                as_of_date=requested_date,
            )

            summaries.append(summary)

        except Exception as error:
            failed_tickers.append(ticker)

            print(
                f"[WARNING] {name}({ticker}) "
                f"시장 데이터 조회 실패: {error}"
            )

    if not summaries:
        raise RuntimeError(
            "시장 데이터 수집에 실패했습니다. "
            f"조회 대상: {len(watchlist)}개, "
            f"실패 종목: {', '.join(failed_tickers)}"
        )

    print(
        f"[Market Collector] "
        f"기준일: {requested_date.isoformat()} / "
        f"성공: {len(summaries)}개 / "
        f"실패: {len(failed_tickers)}개"
    )

    return summaries