import unittest

from app.utils.formatter import (
    format_final_briefing,
    format_interest_compact,
    format_macro_compact,
    format_sector_compact,
)


class FormatterV2Tests(unittest.TestCase):
    def test_macro_deduplication(self):
        text = "시장 흐름: 금리 변화\n시장 흐름: 금리 변화\n시장 흐름: 반도체"
        result = format_macro_compact(text)
        self.assertEqual(result.count("금리 변화"), 1)
        self.assertIn("반도체", result)

    def test_sector_omits_empty_groups_and_keeps_numbers(self):
        text = """강세 흐름
- 확인된 종목은 없습니다.

주의 관찰
- 삼성전자(005930): 모멘텀 점수 -12.5, 1개월 -3.2%, 3개월 -7.1%, 1년 1.0%

약세 흐름
- 확인된 종목은 없습니다."""
        result = format_sector_compact(text)
        self.assertIn("주의 관찰 (1개)", result)
        self.assertIn("모멘텀 점수 -12.5", result)
        self.assertIn("1개월 -3.2%", result)
        self.assertNotIn("강세 흐름", result)
        self.assertNotIn("약세 흐름", result)

    def test_interest_preserves_candidate_evidence(self):
        text = """오늘의 관심 종목 TOP5
① 예시기업(123456)
구분: 뉴스 기반 관심 종목
선정 근거:
- 뉴스 언급: 2회
- 등락률: 5.5%
- 관심도 점수: 7.5"""
        result = format_interest_compact(text)
        self.assertIn("예시기업(123456)", result)
        self.assertIn("뉴스 언급: 2회", result)
        self.assertIn("관심도 점수: 7.5", result)

    def test_empty_interest(self):
        self.assertIn("없습니다", format_interest_compact("오늘의 관심 종목 TOP5\n확인된 관심 후보 종목은 없습니다."))

    def test_final_output_no_internal_logs(self):
        result = format_final_briefing("시장 흐름: 반도체", "주의 관찰\n- 예시기업(123456): 모멘텀 점수 1.0", "", "확인된 흐름을 요약했습니다.")
        self.assertIn("FinSight | AI 시장 브리핑", result)
        self.assertIn("확인된 흐름을 요약했습니다.", result)
        self.assertNotIn("routing_log", result)
        self.assertNotIn("agent_attempts", result)


if __name__ == "__main__":
    unittest.main()
