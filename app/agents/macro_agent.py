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
당신은 한국 경제뉴스를 분석하는 AI 애널리스트입니다.

다음 뉴스 제목만 근거로 현재 경제 이슈를 요약하세요.
없는 사실을 추측하거나 만들어내지 마세요.

[뉴스]
{news_text}

작성 규칙:
- 반드시 한국어만 사용하세요.
- 영어, 중국어, 일본어를 사용하지 마세요.
- 뉴스 제목에 있는 내용만 사용하세요.
- 뉴스와 관련 없는 해석을 추가하지 마세요.
- 투자 추천을 하지 마세요.
- 3~5문장으로 작성하세요.
- 문장은 간결하고 자연스럽게 작성하세요.
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