import unittest
from unittest.mock import patch
from app.agents.supervisor_agent import supervisor_node

TARGET = "app.agents.supervisor_agent.call_supervisor_llm"


def complete():
    return {"agent_attempts": {a: 1 for a in ("macro", "sector", "interest")},
            "agent_status": {a: "success" for a in ("macro", "sector", "interest")},
            **{f"{a}_analysis": "정상 분석" for a in ("macro", "sector", "interest")}}


class SupervisorV2Tests(unittest.TestCase):
    @patch(TARGET)
    def test_pending_without_llm(self, mock):
        state = {}
        for agent in ("macro", "sector", "interest"):
            result = supervisor_node(state)
            self.assertEqual(result["next_agent"], agent)
            state.update(result)
        mock.assert_not_called()

    @patch(TARGET, return_value={"next_agent": "summary", "reason": "충분"})
    def test_quality_review(self, mock):
        result = supervisor_node(complete())
        self.assertEqual(result["decision_source"], "llm")
        self.assertEqual(result["next_agent"], "summary")
        mock.assert_called_once()

    @patch(TARGET, side_effect=RuntimeError("503"))
    def test_failure_remembered(self, mock):
        state = complete()
        state.update(supervisor_node(state))
        self.assertTrue(state["supervisor_llm_disabled"])
        self.assertEqual(supervisor_node(state)["next_agent"], "summary")
        mock.assert_called_once()

    @patch(TARGET, return_value={"next_agent": "macro", "reason": "근거 부족"})
    def test_semantic_retry(self, mock):
        result = supervisor_node(complete())
        self.assertEqual(result["agent_attempts"]["macro"], 2)
        self.assertEqual(result["quality_feedback"]["macro"], "근거 부족")

    @patch(TARGET)
    def test_rule_retry_even_when_disabled(self, mock):
        state = complete()
        state["supervisor_llm_disabled"] = True
        state["agent_status"]["macro"] = "fallback"
        self.assertEqual(supervisor_node(state)["next_agent"], "macro")
        mock.assert_not_called()
