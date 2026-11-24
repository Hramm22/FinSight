import json
import unittest
from unittest.mock import patch

from app.agents.decision_agent import (
    _fact,
    build_decision_context,
    make_decision,
    parse_decision,
)


def state():
    market = [
        {
            "ticker": "005930",
            "name": "삼성전자",
            "month_return": -15.41,
            "three_month_return": -29.73,
            "year_return": 90.51,
        },
        {
            "ticker": "035420",
            "name": "NAVER",
            "month_return": -12.63,
            "three_month_return": -31.61,
            "year_return": -42.55,
        },
    ]

    groups = {
        trend: []
        for trend in ("강세", "긍정 관찰", "중립", "주의 관찰", "약세")
    }

    for stock, trend in zip(market, ("주의 관찰", "약세")):
        score = round(
            stock["month_return"] * 0.5
            + stock["three_month_return"] * 0.3
            + stock["year_return"] * 0.2,
            2,
        )

        groups[trend].append({
            **stock,
            "momentum_score": score,
        })

    return {
        "market_data": market,
        "sector_data": {"groups": groups},
        "agent_status": {
            "macro": "success",
            "sector": "success",
            "interest": "success",
        },
    }


class DecisionV12Tests(unittest.TestCase):

    def test_verified_classification(self):
        stocks = build_decision_context(state())["verified_stocks"]

        self.assertEqual(
            [stock["trend"] for stock in stocks],
            ["주의 관찰", "약세"],
        )

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_hold_replaces_unverified_reason(self, mocked):
        mocked.return_value = json.dumps({
            "action": "HOLD",
            "reason": "경기 침체로 모두 주의 관찰",
            "evidence": [],
        }, ensure_ascii=False)

        result = make_decision(state())

        self.assertEqual(result["action"], "HOLD")
        self.assertIn("NAVER(035420): 약세", result["reason"])
        self.assertNotIn("경기 침체", result["reason"])

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_invalid_sector_data_blocks_llm(self, mocked):
        test_state = state()

        test_state["sector_data"]["groups"]["약세"][0][
            "momentum_score"
        ] = 999

        result = make_decision(test_state)

        self.assertEqual(result["action"], "NO_ACTION")
        mocked.assert_not_called()

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_missing_sector_data_allows_safe_hold(self, mocked):
        mocked.return_value = json.dumps({
            "action": "HOLD",
            "reason": "확인되지 않은 시장 전망을 근거로 관망합니다.",
            "ticker": "",
            "side": "",
            "evidence": [],
        }, ensure_ascii=False)

        test_state = state()
        test_state.pop("sector_data", None)

        result = make_decision(test_state)

        mocked.assert_called_once()
        self.assertEqual(result["action"], "HOLD")
        self.assertEqual(result["ticker"], "")
        self.assertEqual(result["side"], "")
        self.assertEqual(result["evidence"], [])
        self.assertNotIn(
            "확인되지 않은 시장 전망",
            result["reason"],
        )

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_unverified_trade_evidence_rejected(self, mocked):
        mocked.return_value = json.dumps({
            "action": "PROPOSE_TRADE",
            "reason": "좋은 전망",
            "ticker": "005930",
            "side": "BUY",
            "evidence": ["상승 예상"],
        }, ensure_ascii=False)

        result = make_decision(state())

        self.assertEqual(result["action"], "NO_ACTION")

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_verified_trade_still_only_proposal(self, mocked):
        test_state = state()
        context = build_decision_context(test_state)

        stock = next(
            stock
            for stock in context["verified_stocks"]
            if stock["ticker"] == "005930"
        )

        fact = _fact(stock)

        mocked.return_value = json.dumps({
            "action": "PROPOSE_TRADE",
            "reason": "전망",
            "ticker": "005930",
            "side": "BUY",
            "evidence": [fact],
        }, ensure_ascii=False)

        result = make_decision(test_state)

        self.assertEqual(result["action"], "PROPOSE_TRADE")
        self.assertNotIn("전망", result["reason"])
        self.assertEqual(result["evidence"], [fact])

    @patch("app.agents.decision_agent.call_decision_llm")
    def test_research_does_not_claim_external_search(self, mocked):
        mocked.return_value = json.dumps({
            "action": "RESEARCH",
            "reason": "외부 조사 완료",
            "evidence": None,
        }, ensure_ascii=False)

        result = make_decision(state())

        self.assertEqual(result["action"], "RESEARCH")
        self.assertNotIn("외부 조사 완료", result["reason"])

    def test_legacy_parse_hold(self):
        result = parse_decision(
            '{"action":"HOLD","reason":"관찰"}',
            {"stocks": []},
        )

        self.assertEqual(result["action"], "HOLD")


if __name__ == "__main__":
    unittest.main()