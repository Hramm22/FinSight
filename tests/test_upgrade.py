import unittest
from unittest.mock import patch

from app.agents.macro_agent import analyze_macro, analyze_macro_with_status
from app.agents.supervisor_agent import supervisor_node
from app.graph.briefing_graph import briefing_graph

NEWS = [{"title": "코스피 증시 급락"}]
VALID = {"market_flows": [{"flow": "증시 변동성 확대", "evidence_news": ["코스피 증시 급락"]}]}


class UpgradeTests(unittest.TestCase):
    def test_macro_compatibility(self):
        with patch("app.agents.macro_agent.call_macro_gemini", return_value=VALID):
            self.assertIsInstance(analyze_macro(NEWS), str)

    def test_macro_fallback_status(self):
        with patch("app.agents.macro_agent.call_macro_gemini", side_effect=RuntimeError("503")):
            result = analyze_macro_with_status(NEWS)
        self.assertEqual(result["status"], "fallback")
        self.assertTrue(result["analysis"])

    def test_supervisor_forces_retry(self):
        state = {
            "agent_attempts": {"macro": 1, "sector": 1, "interest": 1},
            "agent_status": {"macro": "fallback", "sector": "success", "interest": "success"},
            "agent_errors": {"macro": "503"},
            "macro_analysis": "대체 분석", "sector_analysis": "정상", "interest_analysis": "정상",
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
                return {"analysis": "대체 분석", "status": "fallback", "error": "503"}
            return {"analysis": "정상 분석", "status": "success", "error": ""}
        def choose(context):
            return {"next_agent": context["pending_agents"][0] if context["pending_agents"] else "summary", "reason": "테스트"}
        with patch("app.graph.briefing_graph.analyze_macro_with_status", side_effect=fake_macro), \
             patch("app.graph.briefing_graph.analyze_sector", return_value="섹터 분석"), \
             patch("app.graph.briefing_graph.get_market_interest_candidates", return_value=[]), \
             patch("app.graph.briefing_graph.analyze_market_interest", return_value="관심 분석"), \
             patch("app.graph.briefing_graph.create_final_summary", return_value="완료"), \
             patch("app.agents.supervisor_agent.call_supervisor_llm", side_effect=choose):
            state = briefing_graph.invoke({"news_data": NEWS, "market_data": []}, config={"recursion_limit": 20})
        self.assertEqual(state["final_summary"], "완료")
        self.assertEqual(state["agent_status"]["macro"], "success")
        self.assertEqual(state["agent_attempts"]["macro"], 2)
        self.assertIn("503", calls[1])

    def test_no_infinite_retry(self):
        state = {
            "agent_attempts": {"macro": 2, "sector": 2, "interest": 2},
            "agent_status": {"macro": "fallback", "sector": "success", "interest": "success"},
            "agent_errors": {"macro": "503"},
        }
        result = supervisor_node(state)
        self.assertEqual(result["next_agent"], "summary")
        self.assertEqual(result["agent_attempts"]["macro"], 2)


if __name__ == "__main__":
    unittest.main()
