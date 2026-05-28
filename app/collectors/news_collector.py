import feedparser


RSS_FEEDS = {
    "연합뉴스 경제": "https://www.yna.co.kr/rss/economy.xml",
    "한국경제": "https://www.hankyung.com/feed/economy",
}


def get_news_from_feed(source_name: str, rss_url: str, limit: int = 5) -> list[dict]:
    feed = feedparser.parse(rss_url)

    news_list = []

    for entry in feed.entries[:limit]:
        news_list.append(
            {
                "source": source_name,
                "title": entry.title,
                "link": entry.link,
            }
        )

    return news_list


def get_all_news() -> list[dict]:
    all_news = []

    for source_name, rss_url in RSS_FEEDS.items():
        news = get_news_from_feed(source_name, rss_url)
        all_news.extend(news)

    return all_news


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
    print(format_news(news))