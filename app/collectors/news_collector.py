import os
import tempfile
import json
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser

RSS_FEEDS = {
    "연합뉴스 경제": "https://www.yna.co.kr/rss/economy.xml",
    "연합뉴스 산업": "https://www.yna.co.kr/rss/industry.xml",
    "연합뉴스 증권": "https://www.yna.co.kr/rss/market.xml",
}


POSITIVE_SCORE_KEYWORDS = {
    "코스피": 5,
    "코스닥": 5,
    "증시": 5,
    "환율": 5,
    "원/달러": 5,
    "금리": 5,
    "국고채": 5,
    "채권": 4,
    "외국인": 4,
    "기관": 4,
    "순매도": 4,
    "순매수": 4,
    "반도체": 4,
    "삼성전자": 4,
    "SK하이닉스": 4,
    "삼전": 4,
    "닉스": 4,
    "특징주": 4,
    "급등": 4,
    "급락": 4,
    "상한가": 4,
    "AI": 3,
    "인공지능": 3,
    "에이전틱": 3,
    "AX": 3,
    "ETF": 3,
    "유상증자": 3,
    "상장폐지": 3,
    "실적": 3,
    "수출": 3,
    "관세": 3,
    "유가": 3,
    "원유": 3,
    "원자재": 3,
    "원전": 3,
    "방산": 3,
    "조선": 3,
    "철강": 3,
    "건설": 3,
    "건축자재": 3,
    "시멘트": 3,
    "전력": 3,
    "전기차": 3,
    "배터리": 3,
    "자동차": 3,
    "현대차": 3,
    "기아": 3,
    "네이버": 3,
    "NAVER": 3,
    "카카오": 3,
    "정책": 2,
    "규제": 2,
    "금감원": 2,
    "거래소": 2,
    "개보위": 2,
    "과징금": 2,
    "제재": 2,
    "공급": 2,
    "투자": 2,
}


NEGATIVE_SCORE_KEYWORDS = {
    "인사": -4,
    "모집": -3,
    "행사": -3,
    "축제": -3,
    "주민": -3,
    "복지": -3,
    "공동주택": -3,
    "복합청사": -3,
    "시세표": -4,
    "[표]": -4,
    "영상": -2,
    "세미나": -2,
    "교육생": -2,
    "후보자": -2,
    "협약": -1,
}


KST = ZoneInfo("Asia/Seoul")

HISTORICAL_NEWS_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "historical"
    / "news.json"
)


def calculate_market_score(title: str) -> tuple[int, list[str]]:
    score = 0
    matched_keywords = []

    for keyword, keyword_score in POSITIVE_SCORE_KEYWORDS.items():
        if keyword in title:
            score += keyword_score
            matched_keywords.append(keyword)

    for keyword, keyword_score in NEGATIVE_SCORE_KEYWORDS.items():
        if keyword in title:
            score += keyword_score
            matched_keywords.append(keyword)

    return score, matched_keywords


def parse_published_at(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("뉴스 발행 시각은 문자열이어야 합니다.")

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            f"잘못된 뉴스 발행 시각: {value}"
        ) from error

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"뉴스 발행 시각에 시간대가 없습니다: {value}"
        )

    return parsed.astimezone(KST)


def parse_simulation_time(as_of_date: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(as_of_date)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "시뮬레이션 날짜 형식이 올바르지 않습니다."
        ) from error

    if parsed.tzinfo is None:
        if parsed.time() == time.min:
            parsed = datetime.combine(
                parsed.date(),
                time(23, 59, 59, 999999),
                tzinfo=KST,
            )
        else:
            raise ValueError(
                "시각을 지정할 때는 시간대가 필요합니다."
            )

    return parsed.astimezone(KST)


def build_news_item(
    source: str,
    title: str,
    link: str,
    published_at: str,
) -> dict:
    published = parse_published_at(published_at)
    score, keywords = calculate_market_score(title)

    return {
        "source": source,
        "title": title,
        "link": link,
        "published_at": published.isoformat(),
        "market_score": score,
        "matched_keywords": keywords,
        "is_market_related": score > 0,
    }


def get_news_from_feed(
    source_name: str,
    rss_url: str,
    limit: int = 10,
) -> list[dict]:
    print(f"[INFO] {source_name} 뉴스 수집 시작")

    feed = feedparser.parse(rss_url)
    news_list = []

    for entry in feed.entries:
        if len(news_list) >= limit:
            break

        published_struct = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
        )

        if published_struct is None:
            print("[WARNING] 발행 시각 없는 뉴스 제외")
            continue

        published = datetime(
            *published_struct[:6],
            tzinfo=timezone.utc,
        ).isoformat()

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        if not title or not link:
            continue

        news_list.append(
            build_news_item(
                source=source_name,
                title=title,
                link=link,
                published_at=published,
            )
        )

    print(f"[INFO] {source_name}: {len(news_list)}개 수집")
    return news_list


def remove_duplicate_news(news_list: list[dict]) -> list[dict]:
    unique_news = []
    seen_links = set()

    for news in news_list:
        link = news["link"]

        if link not in seen_links:
            unique_news.append(news)
            seen_links.add(link)

    return unique_news


def prioritize_market_news(
    news_list: list[dict],
    limit: int = 12,
) -> list[dict]:
    return sorted(
        news_list,
        key=lambda news: news["market_score"],
        reverse=True,
    )[:limit]


def get_all_news() -> list[dict]:
    all_news = []

    for source_name, rss_url in RSS_FEEDS.items():
        news = get_news_from_feed(source_name, rss_url)
        all_news.extend(news)

    unique_news = remove_duplicate_news(all_news)
    return prioritize_market_news(unique_news)


def load_historical_news(
    as_of_date: str,
    path: str | Path = HISTORICAL_NEWS_PATH,
    limit: int = 12,
) -> list[dict]:
    cutoff = parse_simulation_time(as_of_date)
    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"과거 뉴스 파일이 없습니다: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        raw_news = json.load(file)

    if not isinstance(raw_news, list):
        raise ValueError(
            "과거 뉴스 JSON은 리스트 형식이어야 합니다."
        )

    available_news = []

    for index, item in enumerate(raw_news):
        if not isinstance(item, dict):
            raise ValueError(
                f"뉴스 {index}: 딕셔너리가 아닙니다."
            )

        try:
            source = item["source"]
            title = item["title"]
            link = item["link"]
            published_at = item["published_at"]

            if not all(
                isinstance(value, str) and value.strip()
                for value in (source, title, link, published_at)
            ):
                raise ValueError("필수 필드가 비어 있습니다.")

            published = parse_published_at(published_at)

        except (KeyError, ValueError) as error:
            raise ValueError(
                f"뉴스 {index}: 데이터 검증 실패"
            ) from error

        if published > cutoff:
            continue

        available_news.append(
            build_news_item(
                source=source,
                title=title,
                link=link,
                published_at=published_at,
            )
        )

    unique_news = remove_duplicate_news(available_news)
    return prioritize_market_news(unique_news, limit)


def format_news(news_list: list[dict]) -> str:
    output = []

    for news in news_list:
        keywords = (
            ", ".join(news["matched_keywords"])
            if news["matched_keywords"]
            else "-"
        )

        output.append(
            f"""
[{news['source']}]
발행 시각: {news['published_at']}
시장 관련도 점수: {news['market_score']}
매칭 키워드: {keywords}
제목: {news['title']}
링크: {news['link']}
""".strip()
        )

    return "\n\n".join(output)


def collect_all_news(limit_per_feed: int = 10) -> list[dict]:
    all_news = []

    for source_name, rss_url in RSS_FEEDS.items():
        news = get_news_from_feed(
            source_name,
            rss_url,
            limit=limit_per_feed,
        )
        all_news.extend(news)

    return remove_duplicate_news(all_news)


def save_historical_news(
    news_list: list[dict],
    path: str | Path = HISTORICAL_NEWS_PATH,
) -> dict:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    existing_news = []

    if file_path.exists():
        with file_path.open("r", encoding="utf-8-sig") as file:
            existing_news = json.load(file)

        if not isinstance(existing_news, list):
            raise ValueError(
                "기존 뉴스 JSON은 리스트 형식이어야 합니다."
            )

    def validate_news(item: dict) -> dict:
        if not isinstance(item, dict):
            raise ValueError("뉴스 항목은 딕셔너리여야 합니다.")

        required = ("source", "title", "link", "published_at")

        for field in required:
            value = item.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"뉴스 필수 필드 오류: {field}"
                )

        return build_news_item(
            source=item["source"],
            title=item["title"],
            link=item["link"],
            published_at=item["published_at"],
        )

    merged_news = []
    seen_links = set()
    added_count = 0

    for item in existing_news:
        validated = validate_news(item)
        link = validated["link"]

        if link not in seen_links:
            merged_news.append(validated)
            seen_links.add(link)

    for item in news_list:
        validated = validate_news(item)
        link = validated["link"]

        if link not in seen_links:
            merged_news.append(validated)
            seen_links.add(link)
            added_count += 1

    merged_news.sort(key=lambda item: item["published_at"])

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            prefix="news_",
            dir=file_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            json.dump(
                merged_news,
                temporary_file,
                ensure_ascii=False,
                indent=2,
            )

            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, file_path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return {
        "added": added_count,
        "total": len(merged_news),
        "path": str(file_path),
    }


def collect_and_save_news() -> dict:
    news_list = collect_all_news()
    result = save_historical_news(news_list)

    print(
        f"[INFO] 신규 뉴스 {result['added']}건 저장, "
        f"누적 {result['total']}건"
    )

    return result


if __name__ == "__main__":
    result = collect_and_save_news()
    print(f"[INFO] 저장 파일: {result['path']}")