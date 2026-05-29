import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def create_final_summary(macro_analysis: str, sector_analysis: str) -> str:
    prompt = f"""
당신은 한국 주식시장 브리핑을 작성하는 AI 애널리스트입니다.

아래 두 분석 결과만 근거로 사용해 최종 시장 브리핑을 작성하세요.
없는 사실을 추측하거나 만들어내지 마세요.

[거시경제/뉴스 분석]
{macro_analysis}

[종목/섹터 분석]
{sector_analysis}

작성 규칙:
1. 반드시 한국어만 사용하세요.
2. 영어, 중국어, 일본어를 사용하지 마세요.
3. 5~7문장으로 짧고 명확하게 작성하세요.
4. 투자 권유 표현을 사용하지 마세요.
5. "추천", "매수", "매도", "무조건 상승", "확실한 호재", "유망"이라는 표현을 사용하지 마세요.
6. 없는 사실을 만들지 마세요.
7. 뉴스와 종목을 억지로 연결하지 마세요.
8. "관찰됩니다", "확인됩니다", "나타납니다", "참고할 수 있습니다" 같은 표현을 사용하세요.
9. 마지막 문장은 반드시 아래 문구로 끝내세요:
"본 브리핑은 투자 참고용 정보이며, 최종 투자 판단은 사용자에게 있습니다."

출력 형식:
[FinSight AI 시장 브리핑]

시장 요약:
...

강세 흐름:
...

약세/주의 흐름:
...

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