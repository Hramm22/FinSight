import re


DISCLAIMER = (
    "본 브리핑은 투자 참고용 정보이며, "
    "최종 투자 판단은 사용자에게 있습니다."
)


EMPTY_STOCK_LINES = [
    "확인된 종목은 없습니다.",
    "확인된 종목이 없습니다.",
    "해당 종목 없음",
]


def _clean_line(line: str) -> str:
    return line.strip()


def _is_empty_stock_line(line: str) -> bool:
    cleaned = line.replace("- ", "").strip()
    return cleaned in EMPTY_STOCK_LINES


def _extract_stock_name_from_line(line: str) -> str:
    line = line.replace("- ", "").strip()

    if ":" in line:
        return line.split(":", 1)[0].strip()

    if "는 " in line:
        return line.split("는 ", 1)[0].strip()

    if "은 " in line:
        return line.split("은 ", 1)[0].strip()

    return line.strip()


def format_macro_compact(macro_analysis: str) -> str:
    lines = macro_analysis.splitlines()
    output = []

    for line in lines:
        line = _clean_line(line)

        if "시장 흐름:" in line:
            item = line.split("시장 흐름:", 1)[1].strip()

            if item and item not in output:
                output.append(item)

    if not output:
        return "- 확인된 시장 흐름 요약이 없습니다."

    return "\n".join(f"- {item}" for item in output[:4])


def format_sector_compact(sector_analysis: str) -> str:
    lines = sector_analysis.splitlines()

    sections = {
        "강세 흐름": [],
        "긍정 관찰": [],
        "중립 흐름": [],
        "주의 관찰": [],
        "약세 흐름": [],
    }

    current_section = None

    for line in lines:
        line = _clean_line(line)

        if not line:
            continue

        if line in sections:
            current_section = line
            continue

        if current_section and line.startswith("- "):
            if _is_empty_stock_line(line):
                continue

            stock_name = _extract_stock_name_from_line(line)

            if stock_name and stock_name not in sections[current_section]:
                sections[current_section].append(stock_name)

    output = []

    for section, stocks in sections.items():
        output.append(section)

        if stocks:
            for stock in stocks:
                output.append(f"- {stock}")
        else:
            output.append("- 확인된 종목은 없습니다.")

        output.append("")

    return "\n".join(output).strip()


def format_interest_compact(interest_analysis: str) -> str:
    lines = interest_analysis.splitlines()

    news_based = []
    rising_only = []

    current_name = None
    current_type = None

    for line in lines:
        line = _clean_line(line)

        if re.match(r"^[①②③④⑤]\s", line):
            current_name = re.sub(r"^[①②③④⑤]\s*", "", line).strip()
            current_type = None
            continue

        if line.startswith("구분:"):
            current_type = line.replace("구분:", "").strip()

            if current_name:
                if current_type == "뉴스 기반 관심 종목":
                    news_based.append(current_name)
                elif current_type == "단순 급등 종목":
                    rising_only.append(current_name)

    output = []

    output.append("뉴스 기반 관심 종목")
    if news_based:
        output.extend(f"- {name}" for name in news_based)
    else:
        output.append("- 확인된 뉴스 기반 관심 종목은 없습니다.")

    output.append("")

    output.append("단순 급등 종목")
    if rising_only:
        output.extend(f"- {name}" for name in rising_only)
    else:
        output.append("- 확인된 단순 급등 종목은 없습니다.")

    return "\n".join(output).strip()


def format_final_briefing(
    macro_analysis: str,
    sector_analysis: str,
    interest_analysis: str,
    ai_summary: str,
) -> str:
    macro_compact = format_macro_compact(macro_analysis)
    sector_compact = format_sector_compact(sector_analysis)
    interest_compact = format_interest_compact(interest_analysis)

    return f"""
============================================================
FinSight AI 시장 브리핑
============================================================

시장 요약

{macro_compact}

------------------------------------------------------------

시장 데이터 흐름

{sector_compact}

------------------------------------------------------------

시장 관심 종목

{interest_compact}

------------------------------------------------------------

AI 종합 브리핑

{ai_summary}

------------------------------------------------------------

투자 유의

{DISCLAIMER}
""".strip()