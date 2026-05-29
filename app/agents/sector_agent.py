import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def analyze_sector(market_data: list) -> str:
    market_text = "\n".join(
        [
            f"{stock['name']} "
            f"(1개월:{stock['month_return']}%, "
            f"3개월:{stock['three_month_return']}%)"
            for stock in market_data
        ]
    )

    prompt = f"""
당신은 주식시장 분석가입니다.

다음 종목 데이터를 분석하세요.

[시장 데이터]
{market_text}

규칙:
- 강세 종목
- 약세 종목
- 시장 특징

3~5문장으로 작성하세요.
"""

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