import re


DISCLAIMER = (
    "본 브리핑은 투자 참고용 정보이며, "
    "최종 투자 판단은 사용자에게 있습니다."
)

EMPTY_STOCK_LINES = {
    "확인된 종목은 없습니다.",
    "확인된 종목이 없습니다.",
    "해당 종목 없음",
}

SECTOR_HEADINGS = (
    "강세 흐름",
    "긍정 관찰",
    "중립 흐름",
    "주의 관찰",
    "약세 흐름",
)



def _clean_line(line: str) -> str:
    return line.strip()


def _is_empty_stock_line(line: str) -> bool:
    return line.removeprefix("- ").strip() in EMPTY_STOCK_LINES


def _extract_stock_name_from_line(line: str) -> str:
    line = line.removeprefix("- ").strip()
    if ":" in line:
        return line.split(":", 1)[0].strip()
    if "는 " in line:
        return line.split("는 ", 1)[0].strip()
    if "은 " in line:
        return line.split("은 ", 1)[0].strip()
    return line


def format_macro_compact(macro_analysis: str) -> str:
    flows = []
    for raw in macro_analysis.splitlines():
        line = _clean_line(raw)
        if "시장 흐름:" not in line:
            continue
        item = line.split("시장 흐름:", 1)[1].strip()
        if item and item not in flows:
            flows.append(item)
    if not flows:
        return "확인된 주요 시장 흐름이 없습니다."
    return "\n".join(f"{index}. {flow}" for index, flow in enumerate(flows[:4], 1))


def format_sector_compact(sector_analysis: str) -> str:
    sections = {heading: [] for heading in SECTOR_HEADINGS}
    current = None
    for raw in sector_analysis.splitlines():
        line = _clean_line(raw)
        if line in sections:
            current = line
            continue
        if not line:
            continue
        if current is not None and line.startswith("- "):
            if _is_empty_stock_line(line):
                continue
            # 원본의 수익률과 모멘텀을 지우지 않고 그대로 보존한다.
            entry = line[2:].strip()
            if entry and entry not in sections[current]:
                sections[current].append(entry)
    active = [(heading, items) for heading, items in sections.items() if items]
    if not active:
        return "분석 가능한 종목이 없습니다."
    output = []
    for heading, items in active:
        output.append(f"■ {heading} ({len(items)}개)")
        output.extend(f"  • {item}" for item in items)
        output.append("")
    return "\n".join(output).strip()


def format_interest_compact(interest_analysis: str) -> str:
    candidates = []
    current = None
    for raw in interest_analysis.splitlines():
        line = _clean_line(raw)
        match = re.match(r"^([①②③④⑤])\s+(.+)$", line)
        if match:
            if current is not None:
                candidates.append(current)
            current = {"rank": match.group(1), "name": match.group(2), "type": "", "details": []}
            continue
        if current is None:
            continue
        if line.startswith("구분:"):
            current["type"] = line.split(":", 1)[1].strip()
        elif line.startswith("- 뉴스 언급:") or line.startswith("- 등락률:") or line.startswith("- 관심도 점수:"):
            current["details"].append(line[2:].strip())
    if current is not None:
        candidates.append(current)
    if not candidates:
        return "오늘 확인된 관심 후보 종목이 없습니다."
    output = []
    for item in candidates[:5]:
        output.append(f"{item['rank']} {item['name']}")
        if item["type"]:
            output.append(f"   {item['type']}")
        if item["details"]:
            output.append("   " + " | ".join(item["details"]))
        output.append("")
    return "\n".join(output).strip()




def format_decision_section(
    decision: dict | None,
    research_result: dict | None = None,
    trade_proposal: dict | None = None,
) -> str:
    """검증된 결정 구조를 사용자용 문장으로 표시한다. 거래는 실행하지 않는다."""
    if not isinstance(decision, dict):
        return "AI 판단 결과를 확인할 수 없습니다."
    action = decision.get("action", "NO_ACTION")
    reason = str(decision.get("reason") or "판단 근거가 제공되지 않았습니다.").strip()
    labels = {
        "HOLD": "관망 (HOLD)",
        "RESEARCH": "추가 확인 필요 (RESEARCH)",
        "PROPOSE_TRADE": "모의거래 제안 (PROPOSE_TRADE)",
        "NO_ACTION": "조치 없음 (NO_ACTION)",
    }
    if action not in labels:
        return "AI 판단 상태를 확인할 수 없습니다."
    lines = [labels[action], f"근거: {reason}"]
    if action == "RESEARCH":
        lines.append("추가 외부 조사는 아직 수행되지 않았습니다.")
        if isinstance(research_result, dict) and research_result.get("status") == "reviewed":
            lines.append("기존 수집 데이터의 개수만 재확인했습니다.")
    elif action == "PROPOSE_TRADE":
        proposal = trade_proposal if isinstance(trade_proposal, dict) else {}
        if proposal.get("status") == "awaiting_approval":
            ticker = str(proposal.get("ticker") or "미확인")
            side = {"BUY": "매수", "SELL": "매도"}.get(proposal.get("side"), "미확인")
            lines.append(f"대상: {ticker} / 방향: {side}")
            lines.append("승인 대기 중인 제안입니다. 주문은 실행되지 않았습니다.")
        else:
            lines.append("거래 제안은 검증을 통과하지 못했거나 생성되지 않았습니다.")
    return "\n".join(lines)

def format_final_briefing(
    macro_analysis: str,
    sector_analysis: str,
    interest_analysis: str,
    ai_summary: str,
    decision: dict | None = None,
    research_result: dict | None = None,
    trade_proposal: dict | None = None,
) -> str:
    macro = format_macro_compact(macro_analysis)
    sector = format_sector_compact(sector_analysis)
    interest = format_interest_compact(interest_analysis)
    summary = ai_summary.strip() or "종합 요약을 생성하지 못했습니다."
    decision_section = format_decision_section(decision, research_result, trade_proposal)
    decision_block = f"\n05  AI 판단\n{decision_section}\n" if decision is not None else ""
    return f"""FinSight | AI 시장 브리핑
{'=' * 44}

01  오늘의 핵심 시장 흐름
{macro}

02  주요 종목 모멘텀
{sector}

03  관심 종목 TOP5
{interest}

04  AI 종합 요약
{summary}
{decision_block}
{'-' * 44}
※ {DISCLAIMER}"""
