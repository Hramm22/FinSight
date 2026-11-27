
import unittest

from types import SimpleNamespace
from unittest.mock import patch

from app.agents import summary_agent


class SummaryGuardrailTests(unittest.TestCase):

    @staticmethod
    def make_response(text, finish_reason="STOP"):

        return SimpleNamespace(
            text=text,
            candidates=[
                SimpleNamespace(
                    finish_reason=finish_reason,
                )
            ],
        )

    def test_219_characters_accepted(self):

        text = "가" * 219

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=self.make_response(text),
        ) as mock_generate:

            result = summary_agent.call_gemini("TEST")

            self.assertEqual(result, text)
            mock_generate.assert_called_once()

    def test_220_characters_accepted(self):

        text = "가" * 220

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=self.make_response(text),
        ) as mock_generate:

            result = summary_agent.call_gemini("TEST")

            self.assertEqual(result, text)
            mock_generate.assert_called_once()

    def test_221_characters_rejected(self):

        text = "가" * 221

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=self.make_response(text),
        ) as mock_generate:

            with self.assertRaisesRegex(
                ValueError,
                "최대 글자 수",
            ):
                summary_agent.call_gemini("TEST")

            mock_generate.assert_called_once()

    def test_empty_response_rejected(self):

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=self.make_response(""),
        ):

            with self.assertRaisesRegex(
                RuntimeError,
                "응답 내용을 반환하지 않았습니다",
            ):
                summary_agent.call_gemini("TEST")

    def test_whitespace_response_rejected(self):

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=self.make_response(" \n\t "),
        ):

            with self.assertRaisesRegex(
                RuntimeError,
                "응답 내용을 반환하지 않았습니다",
            ):
                summary_agent.call_gemini("TEST")

    def test_max_tokens_finish_reason_rejected(self):

        response = self.make_response(
            "Incomplete summary",
            finish_reason="MAX_TOKENS",
        )

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=response,
        ):

            with self.assertRaisesRegex(
                RuntimeError,
                "MAX_TOKENS",
            ):
                summary_agent.call_gemini("TEST")

    def test_missing_candidates_rejected(self):

        response = SimpleNamespace(
            text="Test summary",
            candidates=[],
        )

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=response,
        ):

            with self.assertRaisesRegex(
                RuntimeError,
                "생성 결과가 없습니다",
            ):
                summary_agent.call_gemini("TEST")

    def test_missing_finish_reason_rejected(self):

        response = self.make_response(
            "Test summary",
            finish_reason=None,
        )

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=response,
        ):

            with self.assertRaisesRegex(
                RuntimeError,
                "종료 사유를 확인할 수 없습니다",
            ):
                summary_agent.call_gemini("TEST")

    def test_length_failure_preserves_analysis(self):

        response = self.make_response("가" * 221)

        decision = {"action": "HOLD"}
        research_result = {"status": "test"}
        trade_proposal = {"status": "awaiting_approval"}

        with patch.object(
            summary_agent,
            "generate_content",
            return_value=response,
        ) as mock_generate:

            with patch.object(
                summary_agent,
                "format_final_briefing",
                return_value="FORMATTED_BRIEFING",
            ) as mock_formatter:

                result = summary_agent.create_final_summary(
                    macro_analysis="Macro test",
                    sector_analysis="Sector test",
                    interest_analysis="Interest test",
                    decision=decision,
                    research_result=research_result,
                    trade_proposal=trade_proposal,
                )

                self.assertEqual(
                    result,
                    "FORMATTED_BRIEFING",
                )

                mock_generate.assert_called_once()

                mock_formatter.assert_called_once_with(
                    macro_analysis="Macro test",
                    sector_analysis="Sector test",
                    interest_analysis="Interest test",
                    ai_summary=summary_agent.FALLBACK_SUMMARY,
                    decision=decision,
                    research_result=research_result,
                    trade_proposal=trade_proposal,
                )


if __name__ == "__main__":
    unittest.main()