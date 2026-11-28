import unittest
from unittest.mock import patch

from app.agents.macro_agent import (
    FALLBACK_NOTICE,
    NO_DATA_NOTICE,
    analyze_macro,
    analyze_macro_with_status,
)
from app.agents.supervisor_agent import supervisor_node
from app.graph.briefing_graph import briefing_graph
from app.utils.formatter import (
    format_macro_compact,
    format_final_briefing,
)


NEWS = [{"title": "코스피 증시 급락"}]

VALID = {
    "market_flows": [
        {
            "flow": "증시 관련 이슈",
            "evidence_news": ["코스피 증시 급락"],
        }
    ]
}


class UpgradeTests(unittest.TestCase):
    def test_macro_compatibility(self):
        with patch(
            "app.agents.macro_agent.call_macro_gemini",
            return_value=VALID,
        ):
            analysis = analyze_macro(NEWS)
            result = analyze_macro_with_status(NEWS)

        self.assertIsInstance(analysis, str)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["error"], "")
        self.assertEqual(analysis, result["analysis"])
        self.assertIn("증시 관련 이슈", analysis)
        self.assertIn("코스피 증시 급락", analysis)
        self.assertNotIn(FALLBACK_NOTICE, analysis)

    def test_macro_fallback_status(self):
        with patch(
            "app.agents.macro_agent.call_macro_gemini",
            side_effect=RuntimeError("503"),
        ):
            result = analyze_macro_with_status(NEWS)

        self.assertEqual(result["status"], "fallback")
        self.assertIn("503", result["error"])
        self.assertIn(FALLBACK_NOTICE, result["analysis"])
        self.assertIn("코스피 증시 급락", result["analysis"])
        self.assertNotIn("시장 흐름:", result["analysis"])

    def test_macro_fallback_preserved_by_formatter(self):
        with patch(
            "app.agents.macro_agent.call_macro_gemini",
            side_effect=RuntimeError("503"),
        ):
            result = analyze_macro_with_status(NEWS)

        compact = format_macro_compact(result["analysis"])

        self.assertIn(FALLBACK_NOTICE, compact)
        self.assertIn("코스피 증시 급락", compact)
        self.assertNotIn("[Macro Agent 분석 실패]", compact)

    def test_macro_no_data_preserved_by_formatter(self):
        with patch(
            "app.agents.macro_agent.call_macro_gemini"
        ) as mocked_call:
            result = analyze_macro_with_status([])

        mocked_call.assert_not_called()

        self.assertEqual(result["status"], "no_data")
        self.assertEqual(
            format_macro_compact(result["analysis"]),
            NO_DATA_NOTICE,
        )

    def test_macro_fallback_preserved_in_final_briefing(self):
        with patch(
            "app.agents.macro_agent.call_macro_gemini",
            side_effect=RuntimeError("503"),
        ):
            result = analyze_macro_with_status(NEWS)

        briefing = format_final_briefing(
            macro_analysis=result["analysis"],
            sector_analysis="",
            interest_analysis="",
            ai_summary="종합 요약 테스트",
        )

        self.assertIn(FALLBACK_NOTICE, briefing)
        self.assertIn("코스피 증시 급락", briefing)
        self.assertNotIn("[Macro Agent 분석 실패]", briefing)

    def test_supervisor_forces_retry(self):
        state = {
            "agent_attempts": {
                "macro": 1,
                "sector": 1,
                "interest": 1,
            },
            "agent_status": {
                "macro": "fallback",
                "sector": "success",
                "interest": "success",
            },
            "agent_errors": {
                "macro": "503",
            },
            "macro_analysis": "대체 분석",
            "sector_analysis": "정상",
            "interest_analysis": "정상",
        }

        result = supervisor_node(state)

        self.assertEqual(result["next_agent"], "macro")
        self.assertEqual(result["agent_attempts"]["macro"], 2)
        self.assertIn("macro", result["quality_feedback"])

    def test_full_graph_fallback_then_success(self):
        calls = []

        def fake_macro(news, feedback=""):
            calls.append(feedback)

            if len(calls) == 1:
                return {
                    "analysis": "대체 분석",
                    "status": "fallback",
                    "error": "503",
                }

            return {
                "analysis": "정상 분석",
                "status": "success",
                "error": "",
            }

        def choose(context):
            return {
                "next_agent": (
                    context["pending_agents"][0]
                    if context["pending_agents"]
                    else "summary"
                ),
                "reason": "테스트",
            }

        with patch(
            "app.graph.briefing_graph.analyze_macro_with_status",
            side_effect=fake_macro,
        ), patch(
            "app.graph.briefing_graph.analyze_sector",
            return_value="섹터 분석",
        ), patch(
            "app.graph.briefing_graph.get_market_interest_candidates",
            return_value=[],
        ), patch(
            "app.graph.briefing_graph.analyze_market_interest",
            return_value="관심 분석",
        ), patch(
            "app.graph.briefing_graph.create_final_summary",
            return_value="완료",
        ), patch(
            "app.agents.supervisor_agent.call_supervisor_llm",
            side_effect=choose,
        ):
            state = briefing_graph.invoke(
                {
                    "news_data": NEWS,
                    "market_data": [],
                },
                config={"recursion_limit": 20},
            )

        self.assertEqual(state["final_summary"], "완료")
        self.assertEqual(state["agent_status"]["macro"], "success")
        self.assertEqual(state["agent_attempts"]["macro"], 2)
        self.assertEqual(len(calls), 2)
        self.assertIn("503", calls[1])

    def test_no_infinite_retry(self):
        state = {
            "agent_attempts": {
                "macro": 2,
                "sector": 2,
                "interest": 2,
            },
            "agent_status": {
                "macro": "fallback",
                "sector": "success",
                "interest": "success",
            },
            "agent_errors": {
                "macro": "503",
            },
        }

        result = supervisor_node(state)

        self.assertEqual(result["next_agent"], "summary")
        self.assertEqual(result["agent_attempts"]["macro"], 2)


if __name__ == "__main__":
    unittest.main()