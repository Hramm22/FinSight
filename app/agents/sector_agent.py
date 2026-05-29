import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def analyze_sector(market_data: list) -> str:
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

    prompt = f"""
당신은 한국 주식시장 데이터를 분석하는 AI입니다.

아래 시장 데이터만 근거로 분석하세요.
뉴스, 산업 전망, 원인 추측은 하지 마세요.

[시장 데이터]
{market_text}

작성 규칙:
- 반드시 한국어만 사용하세요.
- 입력된 종목명과 수치를 그대로 사용하세요.
- 입력에 없는 종목을 언급하지 마세요.
- 입력에 없는 수치를 만들지 마세요.
- 상승 원인이나 하락 원인을 추측하지 마세요.
- "추천", "매수", "매도", "유망"이라는 표현을 사용하지 마세요.
- 4문장 이내로 작성하세요.
- 강세 흐름과 약세 흐름만 구분해서 설명하세요.
""".strip()

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

    return response.json()["response"].strip()