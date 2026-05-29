import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def create_prompt(briefing_data: dict) -> str:
    market_data = briefing_data["market_data"]
    news_data = briefing_data["news_data"]

    market_text = "\n".join(
        [
            f"- {stock['name']}({stock['ticker']}): "
            f"현재가 {stock['current_price']:,}원, "
            f"1개월 {stock['month_return']}%, "
            f"3개월 {stock['three_month_return']}%, "
            f"1년 {stock['year_return']}%"
            for stock in market_data
        ]
    )

    news_text = "\n".join(
        [
            f"- [{news['source']}] {news['title']}"
            for news in news_data[:7]
        ]
    )

    return f"""
당신은 한국 주식시장 브리핑을 작성하는 AI 애널리스트입니다.

아래 시장 데이터와 뉴스 제목만 근거로 사용하세요.
없는 사실을 추측하거나 만들어내지 마세요.

[시장 데이터]
{market_text}

[경제/산업 뉴스]
{news_text}

작성 규칙:
1. 한국어로 작성하세요.
2. 5~7문장으로 짧고 명확하게 작성하세요.
3. 강세 종목과 약세 종목을 각각 언급하세요.
4. 뉴스와 시장 데이터를 억지로 연결하지 마세요.
5. 투자 권유 표현을 사용하지 마세요.
6. "매수", "무조건 상승", "확실한 호재" 같은 표현을 금지합니다.
7. 마지막 문장은 반드시 아래 문구로 끝내세요:
"본 브리핑은 투자 참고용 정보이며, 최종 투자 판단은 사용자에게 있습니다."

출력 형식:
[FinSight AI 시장 브리핑]

시장 요약:
...

강세 흐름:
...

약세/주의 흐름:
...

주요 뉴스:
...

투자 유의:
본 브리핑은 투자 참고용 정보이며, 최종 투자 판단은 사용자에게 있습니다.
""".strip()


def create_summary(briefing_data: dict) -> str:
    prompt = create_prompt(briefing_data)

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()
    result = response.json()

    return result["response"].strip()