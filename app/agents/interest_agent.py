import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def normalize_rate(rate: float) -> float:
    if abs(rate) < 0.05:
        return 0.0
    return round(rate, 2)


def normalize_score(score: float) -> float:
    if abs(score) < 0.05:
        return 0.0
    return round(score, 2)


def get_interest_type(candidate: dict) -> str:
    if candidate["news_count"] > 0:
        return "뉴스 기반 관심 종목"
    return "단순 급등 종목"


def format_stock_name(candidate: dict) -> str:
    name = candidate["name"]
    ticker = candidate["ticker"]

    if ticker:
        return f"{name}({ticker})"

    return name


def get_top_interest_candidates(
    candidates: list[dict],
    limit: int = 5,
) -> list[dict]:
    return sorted(
        candidates,
        key=lambda candidate: candidate["interest_score"],
        reverse=True,
    )[:limit]


def count_candidate_types(candidates: list[dict]) -> tuple[int, int]:
    news_count = len(
        [candidate for candidate in candidates if candidate["news_count"] > 0]
    )

    rising_count = len(
        [candidate for candidate in candidates if candidate["news_count"] == 0]
    )

    return news_count, rising_count


def format_rank_number(index: int) -> str:
    numbers = ["①", "②", "③", "④", "⑤"]

    if 1 <= index <= len(numbers):
        return numbers[index - 1]

    return f"{index}번"


def format_top_candidate(index: int, candidate: dict) -> str:
    rank = format_rank_number(index)
    stock_name = format_stock_name(candidate)
    interest_type = get_interest_type(candidate)
    change_rate = normalize_rate(candidate["change_rate"])
    interest_score = normalize_score(candidate["interest_score"])
    news_count = candidate["news_count"]

    return f"""
{rank} {stock_name}
구분: {interest_type}
선정 근거:
- 뉴스 언급: {news_count}회
- 등락률: {change_rate}%
- 관심도 점수: {interest_score}
""".strip()


def build_top5_section(top_candidates: list[dict]) -> str:
    if not top_candidates:
        return "오늘의 관심 종목 TOP5\n\n확인된 관심 후보 종목은 없습니다."

    output = ["오늘의 관심 종목 TOP5", ""]

    for index, candidate in enumerate(top_candidates, start=1):
        output.append(format_top_candidate(index, candidate))
        output.append("")

    return "\n".join(output).strip()


def call_ollama(prompt: str) -> str:
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


def build_summary_with_llm(
    news_count: int,
    rising_count: int,
) -> str:
    prompt = f"""
당신은 FinSight의 Interest Agent입니다.

아래 TOP5 분류 개수만 근거로 종합 문장을 작성하세요.

뉴스 기반 관심 종목: {news_count}개
단순 급등 종목: {rising_count}개

작성 규칙:
- 종목명은 쓰지 마세요.
- 티커도 쓰지 마세요.
- 입력에 없는 숫자를 만들지 마세요.
- 투자 추천을 하지 마세요.
- 상승 예측이나 하락 예측을 하지 마세요.
- 관심도 점수는 참고 지표라고 설명하세요.
- 반드시 한국어만 사용하세요.
- 아래 4문장 구조를 유지하세요.

출력:
오늘 TOP5 관심 후보는 뉴스 기반 관심 종목 {news_count}개, 단순 급등 종목 {rising_count}개입니다.
뉴스 기반 관심 종목은 뉴스 언급이 함께 확인된 종목입니다.
단순 급등 종목은 뉴스 언급 없이 등락률이 높게 확인된 종목입니다.
관심도 점수는 뉴스 언급 횟수와 등락률을 함께 반영한 참고 지표입니다.
""".strip()

    return call_ollama(prompt)


def analyze_market_interest(candidates: list[dict]) -> str:
    top_candidates = get_top_interest_candidates(candidates)

    news_count, rising_count = count_candidate_types(top_candidates)

    top5_section = build_top5_section(top_candidates)
    summary = build_summary_with_llm(news_count, rising_count)

    return f"""
[Interest Agent 관심 종목 분석]

{top5_section}

종합
{summary}
""".strip()


if __name__ == "__main__":
    from app.collectors.market_interest_collector import (
        get_market_interest_candidates,
    )

    candidates = get_market_interest_candidates()
    analysis = analyze_market_interest(candidates)

    print("=" * 60)
    print("Interest Agent 결과")
    print("=" * 60)
    print(analysis)