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


def get_news_from_feed(
    source_name: str,
    rss_url: str,
    limit: int = 10,
) -> list[dict]:
    print(f"\n[{source_name}] 뉴스 수집 시작...")

    feed = feedparser.parse(rss_url)
    news_list = []

    if not feed.entries:
        print(f"[WARNING] {source_name} 뉴스 데이터를 가져오지 못했습니다.")
        return news_list

    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link

        market_score, matched_keywords = calculate_market_score(title)

        news_list.append(
            {
                "source": source_name,
                "title": title,
                "link": link,
                "market_score": market_score,
                "matched_keywords": matched_keywords,
                "is_market_related": market_score > 0,
            }
        )

    print(f"[SUCCESS] {source_name} 뉴스 {len(news_list)}개 수집 완료")

    return news_list


def remove_duplicate_news(news_list: list[dict]) -> list[dict]:
    unique_news = []
    seen_links = set()

    for news in news_list:
        if news["link"] not in seen_links:
            unique_news.append(news)
            seen_links.add(news["link"])

    return unique_news


def prioritize_market_news(
    news_list: list[dict],
    limit: int = 12,
) -> list[dict]:
    sorted_news = sorted(
        news_list,
        key=lambda news: news["market_score"],
        reverse=True,
    )

    return sorted_news[:limit]


def get_all_news() -> list[dict]:
    all_news = []

    for source_name, rss_url in RSS_FEEDS.items():
        news = get_news_from_feed(
            source_name,
            rss_url,
        )
        all_news.extend(news)

    print(f"\n[INFO] 중복 제거 전 뉴스 개수: {len(all_news)}")

    unique_news = remove_duplicate_news(all_news)

    print(f"[INFO] 중복 제거 후 뉴스 개수: {len(unique_news)}")

    prioritized_news = prioritize_market_news(unique_news)

    print(f"[INFO] 시장 관련도 점수 정렬 후 뉴스 개수: {len(prioritized_news)}")

    return prioritized_news


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
시장 관련도 점수: {news['market_score']}
매칭 키워드: {keywords}
제목: {news['title']}
링크: {news['link']}
""".strip()
        )

    return "\n\n".join(output)


if __name__ == "__main__":
    news = get_all_news()

    print("\n" + "=" * 60)
    print("경제/시장 뉴스 수집 결과")
    print("=" * 60)

    print(format_news(news))