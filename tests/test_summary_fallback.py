import unittest
from unittest.mock import patch

from app.agents.summary_agent import FALLBACK_SUMMARY, create_final_summary


class SummaryFallbackTests(unittest.TestCase):
    @patch("app.agents.summary_agent.format_final_briefing")
    @patch("app.agents.summary_agent.create_ai_commentary")
    def test_success_preserves_ai_summary(self, mock_ai, mock_formatter):
        mock_ai.return_value = "정상 요약"
        mock_formatter.return_value = "완성된 브리핑"
        result = create_final_summary("매크로", "섹터", "관심", decision={"action": "HOLD"})
        self.assertEqual(result, "완성된 브리핑")
        self.assertEqual(mock_formatter.call_args.kwargs["ai_summary"], "정상 요약")
        self.assertEqual(mock_formatter.call_args.kwargs["decision"], {"action": "HOLD"})

    @patch("app.agents.summary_agent.format_final_briefing")
    @patch("app.agents.summary_agent.create_ai_commentary", side_effect=RuntimeError("503"))
    def test_api_failure_uses_safe_fallback(self, mock_ai, mock_formatter):
        mock_formatter.return_value = "대체 브리핑"
        result = create_final_summary("매크로", "섹터", "관심")
        self.assertEqual(result, "대체 브리핑")
        self.assertEqual(mock_formatter.call_args.kwargs["ai_summary"], FALLBACK_SUMMARY)
        self.assertNotIn("삼성전자", FALLBACK_SUMMARY)

    @patch("app.agents.summary_agent.format_final_briefing", side_effect=ValueError("formatter error"))
    @patch("app.agents.summary_agent.create_ai_commentary", return_value="정상 요약")
    def test_formatter_error_is_not_hidden(self, mock_ai, mock_formatter):
        with self.assertRaisesRegex(ValueError, "formatter error"):
            create_final_summary("매크로", "섹터", "관심")


if __name__ == "__main__":
    unittest.main()
