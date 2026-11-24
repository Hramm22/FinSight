import unittest
from unittest.mock import patch

from app.utils.formatter import format_decision_section, format_final_briefing


class SummaryV2Tests(unittest.TestCase):
    def test_hold_visible(self):
        text = format_final_briefing("", "", "", "요약", decision={"action": "HOLD", "reason": "단기 수익률 하락"})
        self.assertIn("관망 (HOLD)", text)
        self.assertIn("단기 수익률 하락", text)

    def test_legacy_call_still_works(self):
        text = format_final_briefing("", "", "", "요약")
        self.assertNotIn("05  AI 판단", text)

    def test_research_not_claimed_as_external(self):
        text = format_decision_section({"action": "RESEARCH", "reason": "재확인 필요"}, {"status": "reviewed"})
        self.assertIn("외부 조사는 아직 수행되지 않았습니다", text)

    def test_trade_awaiting_approval(self):
        text = format_decision_section(
            {"action": "PROPOSE_TRADE", "reason": "검토", "ticker": "005930", "side": "BUY"},
            trade_proposal={"status": "awaiting_approval", "ticker": "005930", "side": "BUY"},
        )
        self.assertIn("승인 대기", text)
        self.assertIn("주문은 실행되지 않았습니다", text)

    def test_rejected_proposal_not_shown_as_approved(self):
        text = format_decision_section({"action": "PROPOSE_TRADE", "reason": "검토"},
            trade_proposal={"status": "rejected"})
        self.assertIn("검증을 통과하지 못했거나", text)
        self.assertNotIn("승인 대기 중", text)

    def test_unknown_action_safe(self):
        self.assertIn("확인할 수 없습니다", format_decision_section({"action": "INVALID"}))

    def test_no_action(self):
        self.assertIn("조치 없음", format_decision_section({"action": "NO_ACTION", "reason": "자료 부족"}))


if __name__ == "__main__":
    unittest.main()
