import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def analyze_market_interest(candidates: list[dict]) -> str:
    candidate_text = "\n".join(
        [
            f"- {candidate['name']}({candidate['ticker']}): "
            f"등락률 {candidate['change_rate']}%, "
            f"뉴스 언급 {candidate['news_count']}회, "
            f"관심도 점수 {candidate['interest_score']}"
            for candidate in candidates[:10]
        ]
    )

    prompt = f"""
당신은 한국 주식시장 관심 종목을 분석하는 AI Agent입니다.

아래 데이터는 뉴스 언급 횟수와 상승률을 기반으로 계산한 관심 종목 후보입니다.
이 데이터만 근거로 오늘 시장에서 주목할 만한 종목 흐름을 요약하세요.

[관심 종목 후보]
{candidate_text}

작성 규칙:
- 반드시 한국어만 사용하세요.
- 입력 데이터에 없는 종목을 언급하지 마세요.
- 입력 데이터에 없는 수치를 만들지 마세요.
- 투자 추천을 하지 마세요.
- "매수", "매도", "추천", "유망" 표현을 사용하지 마세요.
- 관심도 점수가 높은 종목을 중심으로 설명하세요.
- 뉴스 언급이 있는 종목과 단순 급등 종목을 구분하세요.
- 5문장 이내로 작성하세요.
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


if __name__ == "__main__":
    from app.collectors.market_interest_collector import (
        get_market_interest_candidates,
    )

    candidates = get_market_interest_candidates()
    analysis = analyze_market_interest(candidates)

    print("=" * 60)
    print("시장 관심도 Agent 분석")
    print("=" * 60)
    print(analysis)