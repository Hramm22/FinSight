import feedparser


RSS_FEEDS = {
    "연합뉴스 경제": "https://www.yna.co.kr/rss/economy.xml",
    "연합뉴스 산업": "https://www.yna.co.kr/rss/industry.xml",
}


def get_news_from_feed(source_name: str, rss_url: str, limit: int = 5) -> list[dict]:
    print(f"\n[{source_name}] 뉴스 수집 시작...")

    feed = feedparser.parse(rss_url)

    news_list = []

    if not feed.entries:
        print(f"[WARNING] {source_name} 뉴스 데이터를 가져오지 못했습니다.")
        return news_list

    for entry in feed.entries[:limit]:
        news_list.append(
            {
                "source": source_name,
                "title": entry.title,
                "link": entry.link,
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


def get_all_news() -> list[dict]:
    all_news = []

    for source_name, rss_url in RSS_FEEDS.items():
        news = get_news_from_feed(source_name, rss_url)
        all_news.extend(news)

    print(f"\n[INFO] 중복 제거 전 뉴스 개수: {len(all_news)}")

    unique_news = remove_duplicate_news(all_news)

    print(f"[INFO] 중복 제거 후 뉴스 개수: {len(unique_news)}")

    return unique_news


def format_news(news_list: list[dict]) -> str:
    output = []

    for news in news_list:
        output.append(
            f"""
[{news['source']}]
제목: {news['title']}
링크: {news['link']}
""".strip()
        )

    return "\n\n".join(output)


if __name__ == "__main__":
    news = get_all_news()

    print("\n" + "=" * 60)
    print("경제 뉴스 수집 결과")
    print("=" * 60)

    print(format_news(news))