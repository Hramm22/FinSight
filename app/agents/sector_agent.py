import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def analyze_sector(market_data: list) -> str:
    market_text = "\n".join(
        [
            f"- {stock['name']}({stock['ticker']}): "
            f"1개월 {stock['month_return']}%, "
            f"3개월 {stock['three_month_return']}%, "
            f"1년 {stock['year_return']}%"
            for stock in market_data
        ]
    )

    prompt = f"""
당신은 한국 주식시장 데이터를 분석하는 AI 애널리스트입니다.

다음 종목 데이터만 근거로 시장 흐름을 분석하세요.
없는 원인이나 배경을 추측하지 마세요.

[시장 데이터]
{market_text}

작성 규칙:
- 반드시 한국어만 사용하세요.
- 영어, 중국어, 일본어를 사용하지 마세요.
- 데이터에 없는 사실을 만들지 마세요.
- 강세 흐름이 관찰되는 종목을 언급하세요.
- 약세 또는 주의 흐름이 관찰되는 종목을 언급하세요.
- 투자 추천을 하지 마세요.
- "추천", "매수", "매도", "유망"이라는 표현을 사용하지 마세요.
- 3~5문장으로 작성하세요.
- "관찰됩니다", "확인됩니다", "나타납니다" 같은 표현을 사용하세요.
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