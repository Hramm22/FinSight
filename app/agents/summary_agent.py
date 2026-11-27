
import os

from dotenv import load_dotenv
from google.genai import types

from app.utils.formatter import format_final_briefing
from app.utils.gemini_client import (
    GeminiPolicy,
    generate_content,
    get_error_status,
)

load_dotenv()

GEMINI_MODEL = os.getenv(
    "SUMMARY_GEMINI_MODEL",
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
)

MAX_OUTPUT_TOKENS = 4096
MAX_SUMMARY_LENGTH = 220

SUMMARY_POLICY = GeminiPolicy(
    timeout_ms=90000,
    max_retries=1,
    retry_delay_seconds=1.0,
)

FALLBACK_SUMMARY = (
    "AI 종합 요약을 생성하지 못했습니다. "
    "아래 Macro·Sector·Interest 분석 결과를 직접 확인해 주세요. "
    "이 안내는 AI 분석 결과가 아닙니다."
)


def get_finish_reason(response) -> str:

    candidates = getattr(response, "candidates", None)

    if not candidates:
        raise RuntimeError(
            "Gemini 응답에 생성 결과가 없습니다."
        )

    reason = getattr(
        candidates[0],
        "finish_reason",
        None,
    )

    if reason is None:
        raise RuntimeError(
            "Gemini 응답의 종료 사유를 확인할 수 없습니다."
        )

    return str(
        getattr(reason, "name", reason)
    ).upper()


def call_gemini(prompt: str) -> str:

    response = generate_content(
        agent_name="Summary",
        model=GEMINI_MODEL,
        prompt=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
        policy=SUMMARY_POLICY,
    )

    finish_reason = get_finish_reason(response)

    if finish_reason != "STOP":
        raise RuntimeError(
            "Summary Agent 응답이 정상 종료되지 않았습니다. "
            f"종료 사유: {finish_reason}"
        )

    result = (response.text or "").strip()

    if not result:
        raise RuntimeError(
            "Gemini가 응답 내용을 반환하지 않았습니다."
        )

    if len(result) > MAX_SUMMARY_LENGTH:
        raise ValueError(
            "Summary Agent 응답이 최대 글자 수를 초과했습니다. "
            f"현재: {len(result)}자, "
            f"최대: {MAX_SUMMARY_LENGTH}자"
        )

    return result


def create_ai_commentary(
    macro_analysis: str,
    sector_analysis: str,
    interest_analysis: str,
) -> str:

    prompt = f"""당신은 FinSight의 Summary Agent입니다.
다음 세 Agent의 결과만을 바탕으로 사용자가 읽기 쉬운 짧은 요약을 작성하세요.
새로운 분석, 숫자, 종목, 뉴스, 원인, 전망, 투자 의견을 만들지 마세요.
확인되지 않은 사실은 단정하지 마세요.

[Macro Agent]
{macro_analysis}

[Sector Agent]
{sector_analysis}

[Interest Agent]
{interest_analysis}

작성 규칙:
- 한국어로 2~3문장, 전체 220자 이내로 작성하세요.
- 서로 다른 핵심 사실을 선택하고 같은 내용을 반복하지 마세요.
- 각 Agent 결과를 반드시 한 문장씩 설명할 필요는 없습니다.
- 관심 후보가 없다면 필요할 때만 한 번 언급하세요.
- 입력에 없는 수치나 종목을 새로 만들지 마세요.
- 원인 추측, 상승·하락 예측, 투자 추천, 매수·매도 지시는 금지합니다.
- 제목, 번호, 불릿 없이 본문만 출력하세요.

추가 사실 검증 규칙:
- 기간별 수익률과 현재 모멘텀 점수를 구분하세요.
- 과거 모멘텀 점수가 없다면 점수의 상승이나 하락을 단정하지 마세요.
- Sector Agent의 종목 분류 결과를 그대로 유지하세요.
- 수익률을 설명할 때는 반드시 해당 기간을 명시하세요.
- 뉴스 언급과 관심도 점수를 실제 시장 참여자의 관심으로 확대 해석하지 마세요.
- 뉴스에서 확인된 이슈를 시장의 원인이나 영향으로 단정하지 마세요.
- 분석 실패, 데이터 부족, 분석 결과 없음을 구분하고 입력에 명시된 상태와 사유를 그대로 유지하세요.
- 기간별 수익률을 나열하기보다 Sector Agent의 종목 분류 결과를 우선하여 요약하세요.
"""

    return call_gemini(prompt)


def create_final_summary(
    macro_analysis: str,
    sector_analysis: str,
    interest_analysis: str,
    decision: dict | None = None,
    research_result: dict | None = None,
    trade_proposal: dict | None = None,
) -> str:

    try:
        ai_summary = create_ai_commentary(
            macro_analysis,
            sector_analysis,
            interest_analysis,
        )

    except Exception as error:

        status = get_error_status(error)

        print(
            "[WARNING] Summary Agent 요약 실패, "
            "대체 안내 사용: "
            f"{type(error).__name__} "
            f"(status={status})"
        )

        ai_summary = FALLBACK_SUMMARY

    return format_final_briefing(
        macro_analysis=macro_analysis,
        sector_analysis=sector_analysis,
        interest_analysis=interest_analysis,
        ai_summary=ai_summary,
        decision=decision,
        research_result=research_result,
        trade_proposal=trade_proposal,
    )