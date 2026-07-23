import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


TREND_ORDER = ["강세", "긍정 관찰", "중립", "주의 관찰", "약세"]


def calculate_momentum_score(stock: dict) -> float:
    score = (
        stock["month_return"] * 0.5
        + stock["three_month_return"] * 0.3
        + stock["year_return"] * 0.2
    )
    return round(score, 2)


def classify_stock_trend(stock: dict) -> str:
    score = calculate_momentum_score(stock)
    month_return = stock["month_return"]
    three_month_return = stock["three_month_return"]

    if score >= 30 and month_return >= 0:
        return "강세"

    if score >= 10:
        return "긍정 관찰"

    if score <= -20:
        return "약세"

    if month_return <= -10 or three_month_return <= -10:
        return "주의 관찰"

    return "중립"


def build_sector_json(market_data: list[dict]) -> dict:
    grouped = {trend: [] for trend in TREND_ORDER}

    for stock in market_data:
        trend = classify_stock_trend(stock)

        grouped[trend].append({
            "name": stock["name"],
            "ticker": stock["ticker"],
            "current_price": stock["current_price"],
            "month_return": stock["month_return"],
            "three_month_return": stock["three_month_return"],
            "year_return": stock["year_return"],
            "momentum_score": calculate_momentum_score(stock),
        })

    return {
        "groups": grouped,
        "distribution": {
            trend: len(grouped[trend])
            for trend in TREND_ORDER
        }
    }


def call_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["response"].strip()


def clean_llm_text(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = text.replace("```", "")
    return text.strip()


def format_sector_report(sector_data: dict, llm_comment: str | None = None) -> str:
    groups = sector_data["groups"]
    distribution = sector_data["distribution"]

    lines = []
    lines.append("[Sector Agent 시장 데이터 분석]")
    lines.append("")

    title_map = {
        "강세": "강세 흐름",
        "긍정 관찰": "긍정 관찰",
        "중립": "중립 흐름",
        "주의 관찰": "주의 관찰",
        "약세": "약세 흐름",
    }

    for trend in TREND_ORDER:
        lines.append(title_map[trend])

        stocks = groups[trend]

        if not stocks:
            lines.append("- 확인된 종목은 없습니다.")
        else:
            for stock in stocks:
                lines.append(
                    f"- {stock['name']}({stock['ticker']}): "
                    f"모멘텀 점수 {stock['momentum_score']}, "
                    f"1개월 {stock['month_return']}%, "
                    f"3개월 {stock['three_month_return']}%, "
                    f"1년 {stock['year_return']}%"
                )

        lines.append("")

    lines.append("종합")
    lines.append(
        f"시장 데이터에서는 강세 {distribution['강세']}개, "
        f"긍정 관찰 {distribution['긍정 관찰']}개, "
        f"중립 {distribution['중립']}개, "
        f"주의 관찰 {distribution['주의 관찰']}개, "
        f"약세 {distribution['약세']}개 종목이 확인되었습니다."
    )

    if llm_comment:
        lines.append("")
        lines.append("Sector Agent 코멘트")
        lines.append(clean_llm_text(llm_comment))

    return "\n".join(lines).strip()


def analyze_sector(market_data: list[dict]) -> str:
    sector_data = build_sector_json(market_data)

    prompt = f"""
당신은 FinSight의 Sector Agent입니다.

아래 JSON은 코드가 계산한 종목 분류 결과입니다.
당신은 분류를 변경하지 말고, 결과를 2~3문장으로 요약만 하세요.

절대 규칙:
- JSON에 없는 종목을 추가하지 마세요.
- 분류를 바꾸지 마세요.
- 숫자를 새로 만들지 마세요.
- 투자 추천, 매수, 매도 표현을 쓰지 마세요.
- 전망이나 원인 추측을 하지 마세요.
- 반드시 한국어로 작성하세요.
- 종목명은 JSON에 있는 이름만 사용하세요.

분류 결과 JSON:
{json.dumps(sector_data, ensure_ascii=False, indent=2)}
""".strip()

    try:
        llm_comment = call_ollama(prompt)
    except Exception:
        llm_comment = None

    return format_sector_report(sector_data, llm_comment)


if __name__ == "__main__":
    from app.collectors.market_collector import get_watchlist_summaries

    market_data = get_watchlist_summaries()

    print("=" * 60)
    print("Sector Agent 결과")
    print("=" * 60)

    print(analyze_sector(market_data))