import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def create_final_summary(macro_analysis: str, sector_analysis: str) -> str:
    prompt = f"""
당신은 금융 데이터를 요약하는 AI입니다.

아래 두 분석 결과만 근거로 최종 브리핑을 작성하세요.
새로운 사실, 새로운 숫자, 새로운 종목을 만들지 마세요.

[뉴스/거시 분석]
{macro_analysis}

[시장 데이터 분석]
{sector_analysis}

중요 규칙:
- 반드시 한국어만 사용하세요.
- 입력에 없는 종목명을 언급하지 마세요.
- 입력에 없는 숫자를 생성하지 마세요.
- 입력된 숫자를 변경하지 마세요.
- 뉴스와 종목을 억지로 연결하지 마세요.
- 원인, 이유, 영향 관계를 추측하지 마세요.
- "때문에", "영향으로", "원인으로" 표현을 사용하지 마세요.
- "추천", "매수", "매도", "유망", "확실한 호재", "무조건 상승" 표현을 사용하지 마세요.
- 투자 권유를 하지 마세요.
- 모든 항목을 비우지 말고 작성하세요.
- 각 항목은 1~2문장으로 작성하세요.
- 마지막 문장은 반드시 아래 문구로 끝내세요:
"본 브리핑은 투자 참고용 정보이며, 최종 투자 판단은 사용자에게 있습니다."

출력 형식:
[FinSight AI 시장 브리핑]

시장 요약:
뉴스/거시 분석과 시장 데이터 분석에서 확인되는 내용을 요약하세요.

강세 흐름:
강세 흐름이 관찰되는 종목과 수치를 요약하세요.

약세/주의 흐름:
약세 또는 주의 흐름이 관찰되는 종목과 수치를 요약하세요.

주요 분석:
뉴스와 시장 데이터를 억지로 연결하지 말고, 각각 확인된 사실만 정리하세요.

투자 유의:
본 브리핑은 투자 참고용 정보이며, 최종 투자 판단은 사용자에게 있습니다.
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