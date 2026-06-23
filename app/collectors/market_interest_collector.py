import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from app.collectors.news_collector import get_all_news


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MARKETS = {
    0: "KOSPI",
    1: "KOSDAQ",
}

WATCHLIST_NAMES = [
    "삼성전자",
    "SK하이닉스",
    "NAVER",
    "카카오",
    "현대차",
    "기아",
    "LG전자",
    "LG에너지솔루션",
    "삼성SDI",
    "삼성바이오로직스",
    "셀트리온",
    "두산에너빌리티",
    "한화에어로스페이스",
    "한국항공우주",
    "HD현대중공업",
    "POSCO홀딩스",
]

EXCLUDE_KEYWORDS = [
    "ETF",
    "ETN",
    "KODEX",
    "TIGER",
    "ACE",
    "SOL",
    "RISE",
    "KIWOOM",
    "KBSTAR",
    "HANARO",
    "ARIRANG",
    "KOSEF",
    "TIMEFOLIO",
    "레버리지",
    "인버스",
    "스팩",
    "SPAC",
    "액티브",
]


def clean_number(value: str) -> int:
    value = value.replace(",", "").strip()
    value = re.sub(r"[^0-9]", "", value)

    if not value:
        return 0

    return int(value)


def clean_percent(value: str) -> float:
    value = (
        value.replace("%", "")
        .replace("+", "")
        .replace(",", "")
        .strip()
    )

    if not value:
        return 0.0

    return float(value)


def is_common_stock(name: str) -> bool:
    upper_name = name.upper()

    if any(keyword in upper_name for keyword in EXCLUDE_KEYWORDS):
        return False

    if name.endswith("우") or "우B" in name or "우선주" in name:
        return False

    return True


def parse_naver_rise_page(
    url: str,
    market: str,
) -> list[dict]:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.encoding = "euc-kr"

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.select_one("table.type_2")

    if table is None:
        return []

    result = []

    for row in table.select("tr"):
        link = row.select_one("a[href*='code=']")
        tds = row.select("td")

        if link is None or len(tds) < 7:
            continue

        href = link.get("href", "")
        match = re.search(r"code=(\d{6})", href)

        if not match:
            continue

        ticker = match.group(1)
        name = link.get_text(strip=True)

        if not is_common_stock(name):
            continue

        current_price = clean_number(tds[2].get_text(strip=True))
        change_rate = clean_percent(tds[4].get_text(strip=True))

        if current_price <= 0:
            continue

        result.append(
            {
                "date": datetime.today().strftime("%Y%m%d"),
                "ticker": ticker,
                "name": name,
                "market": market,
                "current_price": current_price,
                "change_rate": change_rate,
                "reason": "상승률 상위",
            }
        )

    return result


def get_top_by_rising_rate(
    limit: int = 30,
    max_pages: int = 5,
) -> list[dict]:
    stocks = []

    for sosok, market in MARKETS.items():
        for page in range(1, max_pages + 1):
            url = (
                "https://finance.naver.com/sise/sise_rise.naver"
                f"?sosok={sosok}&page={page}"
            )

            page_stocks = parse_naver_rise_page(
                url,
                market,
            )

            stocks.extend(page_stocks)

            if len(stocks) >= limit:
                return stocks[:limit]

    return stocks[:limit]


def count_news_mentions(
    news_data: list[dict],
    stock_names: list[str],
) -> dict:
    mention_counts = {
        stock_name: 0
        for stock_name in stock_names
    }

    for news in news_data:
        title = news["title"]

        for stock_name in stock_names:
            if stock_name in title:
                mention_counts[stock_name] += 1

    return mention_counts


def calculate_interest_score(
    news_count: int,
    change_rate: float,
) -> float:
    score = (news_count * 30) + (max(change_rate, 0) * 0.5)

    return round(score, 2)


def get_market_interest_candidates(
    news_data: list[dict] | None = None,
) -> list[dict]:
    if news_data is None:
        news_data = get_all_news()

    rising_stocks = get_top_by_rising_rate(limit=30)

    stock_names = list(
        set(
            WATCHLIST_NAMES
            + [
                stock["name"]
                for stock in rising_stocks
            ]
        )
    )

    mention_counts = count_news_mentions(
        news_data,
        stock_names,
    )

    candidates = []

    for stock_item in rising_stocks:
        name = stock_item["name"]
        news_count = mention_counts.get(name, 0)

        candidates.append(
            {
                "ticker": stock_item["ticker"],
                "name": name,
                "market": stock_item["market"],
                "current_price": stock_item["current_price"],
                "change_rate": stock_item["change_rate"],
                "news_count": news_count,
                "interest_score": calculate_interest_score(
                    news_count,
                    stock_item["change_rate"],
                ),
                "reason": "상승률 상위 + 뉴스 언급 기반",
            }
        )

    for stock_name, news_count in mention_counts.items():
        if news_count <= 0:
            continue

        already_exists = any(
            candidate["name"] == stock_name
            for candidate in candidates
        )

        if already_exists:
            continue

        candidates.append(
            {
                "ticker": None,
                "name": stock_name,
                "market": None,
                "current_price": None,
                "change_rate": 0.0,
                "news_count": news_count,
                "interest_score": calculate_interest_score(
                    news_count,
                    0.0,
                ),
                "reason": "뉴스 언급 기반",
            }
        )

    candidates.sort(
        key=lambda item: item["interest_score"],
        reverse=True,
    )

    return candidates


def format_market_interest_candidates(
    candidates: list[dict],
    limit: int = 15,
) -> str:
    output = []

    for candidate in candidates[:limit]:
        current_price = (
            f"{candidate['current_price']:,}원"
            if candidate["current_price"] is not None
            else "-"
        )

        ticker = (
            candidate["ticker"]
            if candidate["ticker"] is not None
            else "-"
        )

        market = (
            candidate["market"]
            if candidate["market"] is not None
            else "-"
        )

        output.append(
            f"- {candidate['name']}({ticker}): "
            f"{market} / "
            f"현재가 {current_price} / "
            f"등락률 {candidate['change_rate']}% / "
            f"뉴스 언급 {candidate['news_count']}회 / "
            f"관심도 점수 {candidate['interest_score']} / "
            f"{candidate['reason']}"
        )

    return "\n".join(output)


if __name__ == "__main__":
    candidates = get_market_interest_candidates()

    print("=" * 60)
    print("시장 관심 종목 후보")
    print("=" * 60)

    print(format_market_interest_candidates(candidates))