import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def create_prompt(briefing_data: dict) -> str:
    market_data = briefing_data["market_data"]
    news_data = briefing_data["news_data"]

    market_text = "\n".join(
        [
            f"{stock['name']} - "
            f"1개월 수익률: {stock['month_return']}%, "
            f"3개월 수익률: {stock['three_month_return']}%, "
            f"1년 수익률: {stock['year_return']}%"
            for stock in market_data
        ]
    )

    news_text = "\n".join(
        [
            f"- {news['title']}"
            for news in news_data[:5]
        ]
    )

    prompt = f"""
당신은 금융 시장 분석 AI입니다.

다음 시장 데이터와 경제 뉴스를 기반으로
오늘의 시장 브리핑을 한국어로 작성하세요.

[시장 데이터]
{market_text}

[경제/산업 뉴스]
{news_text}

요구사항:
1. 자연스럽고 전문적인 한국어 사용
2. 핵심 시장 흐름 요약
3. 강세/약세 종목 언급
4. 뉴스와 시장 흐름 연결
5. 5~8문장 정도로 작성
6. 마지막에 투자 유의 문구 추가
"""

    return prompt.strip()


def create_summary(briefing_data: dict) -> str:
    prompt = create_prompt(briefing_data)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        },
    )

    result = response.json()

    return result["response"].strip()