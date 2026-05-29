import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def analyze_macro(news_data: list) -> str:
    news_text = "\n".join(
        [
            f"- {news['title']}"
            for news in news_data[:7]
        ]
    )

    prompt = f"""
당신은 경제 전문 애널리스트입니다.

다음 뉴스 제목들을 분석하여
현재 경제 이슈를 3~5문장으로 요약하세요.

[뉴스]
{news_text}

규칙:
- 추측 금지
- 뉴스에 있는 내용만 사용
- 한국어 사용
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