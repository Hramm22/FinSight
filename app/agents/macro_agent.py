import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


FLOW_CANDIDATES = [
    "증시 변동성 확대",
    "금리 흐름 변화",
    "환율 흐름 변화",
    "반도체 관련 뉴스 집중",
    "AI 관련 기업 뉴스 증가",
    "기업 자금조달·상장관리 이슈",
    "특정 업종 주가 변동",
    "정책·규제 관련 이슈",
    "원자재·유가 흐름",
    "주요 기업 이슈",
    "기타 시장 이슈",
]


def get_gemini_client() -> genai.Client:
    """
    Gemini API 클라이언트를 생성합니다.

    GEMINI_API_KEY가 설정되지 않았으면 명확한 오류를 발생시킵니다.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. "
            ".env 파일 또는 Render 환경 변수에 API 키를 등록해 주세요."
        )

    return genai.Client(api_key=GEMINI_API_KEY)


def normalize_flow_name(flow_name: str) -> str:
    text = str(flow_name).strip()

    if text in FLOW_CANDIDATES:
        return text

    if any(k in text for k in ["코스피", "코스닥", "증시", "혼조", "급락", "급등"]):
        return "증시 변동성 확대"

    if any(k in text for k in ["금리", "국고채", "채권"]):
        return "금리 흐름 변화"

    if any(k in text for k in ["환율", "달러", "원화"]):
        return "환율 흐름 변화"

    if any(k in text for k in ["반도체", "HBM", "메모리"]):
        return "반도체 관련 뉴스 집중"

    if any(k in text for k in ["AI", "인공지능"]):
        return "AI 관련 기업 뉴스 증가"

    if any(
        k in text
        for k in [
            "유상증자",
            "회사채",
            "신종자본증권",
            "IPO",
            "상장",
        ]
    ):
        return "기업 자금조달·상장관리 이슈"

    if any(
        k in text
        for k in [
            "과징금",
            "담합",
            "규제",
            "금융위",
            "공정위",
        ]
    ):
        return "정책·규제 관련 이슈"

    return "기타 시장 이슈"


def extract_json(text: str) -> dict:
    """
    Gemini 응답에서 JSON 객체를 추출합니다.

    JSON 응답 모드를 사용하지만, 예외 상황에 대비해
    코드 블록과 앞뒤 문장을 제거할 수 있도록 유지합니다.
    """
    cleaned_text = text.strip()

    cleaned_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned_text,
        flags=re.IGNORECASE,
    )
    cleaned_text = re.sub(
        r"\s*```$",
        "",
        cleaned_text,
    )

    try:
        parsed = json.loads(cleaned_text)

        if not isinstance(parsed, dict):
            raise ValueError("Gemini 응답의 최상위 구조가 객체가 아닙니다.")

        return parsed

    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned_text)

        if not match:
            raise ValueError("JSON 형식 응답을 찾지 못했습니다.")

        parsed = json.loads(match.group())

        if not isinstance(parsed, dict):
            raise ValueError("Gemini 응답의 최상위 구조가 객체가 아닙니다.")

        return parsed


def make_safe_description(flow: str, evidence_news: list[str]) -> str:
    count = len(evidence_news)

    if count >= 2:
        return f"{flow} 관련 뉴스가 {count}건 함께 확인되었습니다."

    if count == 1:
        return f"{flow} 관련 뉴스가 확인되었습니다."

    return f"{flow} 관련 흐름이 확인되었습니다."


def format_macro_report(data: dict) -> str:
    flows = data.get("market_flows", [])

    if not isinstance(flows, list):
        flows = []

    lines = ["[오늘의 시장 흐름]", ""]

    for idx, item in enumerate(flows[:3], start=1):
        if not isinstance(item, dict):
            continue

        flow = normalize_flow_name(
            item.get("flow", "기타 시장 이슈")
        )

        evidence_news = item.get("evidence_news", [])

        if not isinstance(evidence_news, list):
            evidence_news = []

        evidence_news = [
            str(news).strip()
            for news in evidence_news
            if str(news).strip()
        ]

        lines.append(f"{idx}️⃣ 시장 흐름: {flow}")
        lines.append("근거 뉴스:")

        if evidence_news:
            for news in evidence_news[:4]:
                lines.append(f"- {news}")
        else:
            lines.append("- 확인된 근거 뉴스가 없습니다.")

        lines.append("확인 내용:")
        lines.append(
            make_safe_description(
                flow,
                evidence_news,
            )
        )
        lines.append("")

    summary_flows = []

    for item in flows[:3]:
        if not isinstance(item, dict):
            continue

        normalized_flow = normalize_flow_name(
            item.get("flow", "기타 시장 이슈")
        )

        if normalized_flow not in summary_flows:
            summary_flows.append(normalized_flow)

    lines.append("[Macro Agent 종합]")

    if summary_flows:
        lines.append(
            f"오늘 뉴스에서는 {', '.join(summary_flows)} "
            "흐름이 확인되었습니다."
        )
    else:
        lines.append(
            "오늘 뉴스에서 뚜렷한 시장 흐름을 "
            "확인하기 어렵습니다."
        )

    return "\n".join(lines).strip()


def build_fallback_data(news_titles: list[str]) -> dict:
    """
    Gemini 호출 또는 JSON 파싱 실패 시 사용하는 안전한 기본값입니다.
    """
    return {
        "market_flows": [
            {
                "flow": "기타 시장 이슈",
                "evidence_news": news_titles[:3],
            }
        ]
    }


def analyze_macro(news_data: list[dict]) -> str:
    news_titles = [
        str(news.get("title", "")).strip()
        for news in news_data[:12]
        if isinstance(news, dict)
        and str(news.get("title", "")).strip()
    ]

    if not news_titles:
        return format_macro_report(
            {
                "market_flows": []
            }
        )

    news_text = "\n".join(
        f"- {title}"
        for title in news_titles
    )

    candidates_text = "\n".join(
        f"- {candidate}"
        for candidate in FLOW_CANDIDATES
    )

    prompt = f"""
당신은 FinSight의 Macro Agent입니다.

역할:
뉴스 제목을 보고 오늘 확인되는 시장 흐름을 분류하세요.
문장형 브리핑을 쓰지 말고 반드시 JSON 객체만 출력하세요.

뉴스 목록:
{news_text}

시장 흐름 후보:
{candidates_text}

분류 기준:
- 코스피, 코스닥, 혼조, 급락, 급등 → 증시 변동성 확대
- 국고채, 채권금리, 기준금리 → 금리 흐름 변화
- 환율, 달러, 원화 → 환율 흐름 변화
- 반도체, 메모리, HBM → 반도체 관련 뉴스 집중
- AI, 인공지능 → AI 관련 기업 뉴스 증가
- 유상증자, 회사채, 신종자본증권, IPO, 상장
  → 기업 자금조달·상장관리 이슈
- 과징금, 담합, 금융위, 공정위, 규제
  → 정책·규제 관련 이슈

규칙:
- flow 값은 반드시 시장 흐름 후보 중 하나만 사용하세요.
- evidence_news에는 위 뉴스 목록에 있는 제목만 그대로 넣으세요.
- 뉴스 제목에 없는 원인, 전망, 수치, 해석을 만들지 마세요.
- 최대 3개 흐름만 선택하세요.
- 같은 흐름을 중복 선택하지 마세요.
- 각 흐름에는 관련 있는 뉴스만 넣으세요.
- 반드시 유효한 JSON 객체만 출력하세요.

출력 구조:
{{
  "market_flows": [
    {{
      "flow": "증시 변동성 확대",
      "evidence_news": [
        "뉴스 목록에 실제로 존재하는 제목"
      ]
    }}
  ]
}}
""".strip()

    try:
        client = get_gemini_client()

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        raw_result = (response.text or "").strip()

        if not raw_result:
            raise ValueError("Gemini가 빈 응답을 반환했습니다.")

        data = extract_json(raw_result)

    except Exception as error:
        print(f"[WARNING] Macro Agent Gemini 호출 실패: {error}")
        data = build_fallback_data(news_titles)

    return format_macro_report(data)


if __name__ == "__main__":
    from app.collectors.news_collector import get_all_news

    news = get_all_news()

    print("=" * 60)
    print("Macro Agent 결과")
    print("=" * 60)
    print(analyze_macro(news))