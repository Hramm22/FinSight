import unittest
from unittest.mock import patch

from app.agents.decision_agent import make_decision, parse_decision


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            "agent_status": {"macro": "success", "sector": "success", "interest": "success"},
            "market_data": [{"ticker": "005930", "name": "삼성전자", "current_price": 100,
                             "month_return": 1, "three_month_return": 2, "year_return": 3}],
        }

    def test_invalid_json(self):
        self.assertEqual(parse_decision("not json", {"stocks": []})["action"], "NO_ACTION")

    def test_unknown_ticker(self):
        raw = '{"action":"PROPOSE_TRADE","reason":"검토","ticker":"999999","side":"BUY","evidence":["근거"]}'
        self.assertEqual(parse_decision(raw, {"stocks": [{"ticker": "005930"}]})["action"], "NO_ACTION")

    def test_agent_failure(self):
        self.state["agent_status"]["macro"] = "fallback"
        self.assertEqual(make_decision(self.state)["action"], "NO_ACTION")

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_valid_hold(self, mocked):
        mocked.return_value = '{"action":"HOLD","reason":"관찰 필요","ticker":"","side":"","evidence":[]}'
        self.assertEqual(make_decision(self.state)["action"], "HOLD")

    @patch("app.agents.decision_agent.call_decision_llm", side_effect=RuntimeError("offline"))
    def test_api_failure(self, mocked):
        self.assertEqual(make_decision(self.state)["action"], "NO_ACTION")

    def test_hold_missing_evidence(self):
        raw = '{"action":"HOLD","reason":"관찰 필요","ticker":"","side":""}'
        result = parse_decision(raw, {"stocks": []})
        self.assertEqual(result["action"], "HOLD")
        self.assertEqual(result["evidence"], [])

    def test_research_null_evidence(self):
        raw = '{"action":"RESEARCH","reason":"재확인 필요","evidence":null}'
        self.assertEqual(parse_decision(raw, {"stocks": []})["action"], "RESEARCH")

    def test_trade_missing_evidence_rejected(self):
        raw = '{"action":"PROPOSE_TRADE","reason":"검토","ticker":"005930","side":"BUY"}'
        self.assertEqual(parse_decision(raw, {"stocks": [{"ticker":"005930"}]})["action"], "NO_ACTION")

    def test_trade_valid_evidence(self):
        raw = '{"action":"PROPOSE_TRADE","reason":"검토","ticker":"005930","side":"BUY","evidence":["확인된 수치"]}'
        self.assertEqual(parse_decision(raw, {"stocks": [{"ticker":"005930"}]})["action"], "PROPOSE_TRADE")

    def test_hold_string_evidence_rejected(self):
        raw = '{"action":"HOLD","reason":"관찰 필요","evidence":"문자열"}'
        self.assertEqual(parse_decision(raw, {"stocks": []})["action"], "NO_ACTION")


if __name__ == "__main__":
    unittest.main()
