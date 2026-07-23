import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.utils.formatter import format_final_briefing


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. "
            ".env 파일을 확인하세요."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=500,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini가 응답 내용을 반환하지 않았습니다.")

    return response.text.strip()


def create_ai_commentary(
    macro_analysis: str,
    sector_analysis: str,
    interest_analysis: str,
) -> str:
    prompt = f"""
당신은 FinSight의 Summary Agent입니다.

당신의 역할은 Macro Agent, Sector Agent, Interest Agent의 분석 결과를
사용자에게 전달하는 시장 브리핑 작성자입니다.

새로운 분석을 하지 마세요.
새로운 종목을 만들지 마세요.
새로운 숫자를 만들지 마세요.

========================
Macro Agent 결과
========================

{macro_analysis}

========================
Sector Agent 결과
========================

{sector_analysis}

========================
Interest Agent 결과
========================

{interest_analysis}

========================
절대 규칙
========================

- 반드시 한국어만 사용하세요.
- 입력에 없는 종목명과 숫자를 만들지 마세요.
- 입력된 종목명과 티커를 변경하지 마세요.
- 원인을 추측하지 마세요.
- 미래를 예측하지 마세요.
- 투자 의견을 작성하지 마세요.
- 아래 표현은 사용하지 마세요.

"때문에"
"영향으로"
"원인으로"
"이로 인해"
"이에 따라"
"전망됩니다"
"예상됩니다"
"판단됩니다"
"활용될 수 있습니다"
"추천"
"매수"
"매도"
"호재"
"악재"

========================
작성 방식
========================

총 4문장으로 작성하세요.

① 첫 번째 문장
오늘 시장에서 가장 큰 흐름을 요약하세요.

② 두 번째 문장
Sector Agent의 시장 데이터 흐름을 요약하세요.

③ 세 번째 문장
Interest Agent의 관심 종목 흐름을 요약하세요.

④ 네 번째 문장
오늘 브리핑 전체를 한 문장으로 마무리하세요.

각 문장은 60자 이내로 작성하세요.
불필요한 수식어를 사용하지 마세요.
객관적인 사실만 전달하세요.
""".strip()

    return call_gemini(prompt)


def create_final_summary(
    macro_analysis: str,
    sector_analysis: str,
    interest_analysis: str,
) -> str:
    ai_summary = create_ai_commentary(
        macro_analysis=macro_analysis,
        sector_analysis=sector_analysis,
        interest_analysis=interest_analysis,
    )

    return format_final_briefing(
        macro_analysis=macro_analysis,
        sector_analysis=sector_analysis,
        interest_analysis=interest_analysis,
        ai_summary=ai_summary,
    )