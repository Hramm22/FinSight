import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.agents import macro_agent as macro


NEWS_TITLES = [
    "코스피 외국인 매도에 하락 마감",
    "코스닥 상승 출발 후 혼조세",
    "국고채 3년물 금리 상승",
    "한국은행 기준금리 동결",
    "원달러 환율 상승 마감",
]

NEWS_DATA = [
    {"title": title}
    for title in NEWS_TITLES
]


def make_flow(
    flow="증시 관련 이슈",
    evidence=None,
):
    return {
        "flow": flow,
        "evidence_news": (
            [NEWS_TITLES[0]]
            if evidence is None
            else evidence
        ),
    }


def make_response(
    text,
    finish_reason="STOP",
):
    return SimpleNamespace(
        text=text,
        candidates=[
            SimpleNamespace(
                finish_reason=finish_reason,
            )
        ],
    )


class MacroGuardrailTests(unittest.TestCase):
    def test_prepare_news_filters_invalid_titles(self):
        news = [
            None,
            {},
            {"title": None},
            {"title": 123},
            {"title": ""},
            {"title": "   "},
            {"title": " 코스피 하락 "},
            {"title": "코스피 하락"},
            {"title": "금리 상승"},
        ]

        self.assertEqual(
            macro.prepare_news_titles(news),
            ["코스피 하락", "금리 상승"],
        )

    def test_prepare_news_limits_to_twelve(self):
        news = [
            {"title": f"테스트 뉴스 {index}"}
            for index in range(20)
        ]

        result = macro.prepare_news_titles(news)

        self.assertEqual(len(result), 12)
        self.assertEqual(
            result,
            [f"테스트 뉴스 {index}" for index in range(12)],
        )

    def test_valid_macro_data(self):
        data = {
            "market_flows": [
                make_flow(),
                make_flow(
                    "금리 관련 이슈",
                    NEWS_TITLES[2:4],
                ),
            ]
        }

        result = macro.validate_macro_data(
            data,
            NEWS_TITLES,
        )

        self.assertEqual(result, data)
        self.assertIsNot(
            result["market_flows"][0]["evidence_news"],
            data["market_flows"][0]["evidence_news"],
        )

    def test_reject_invalid_top_level(self):
        for data in [None, [], "invalid", 123]:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    macro.validate_macro_data(
                        data,
                        NEWS_TITLES,
                    )

    def test_reject_invalid_market_flows(self):
        for flows in [None, {}, "invalid", []]:
            with self.subTest(flows=flows):
                with self.assertRaises(ValueError):
                    macro.validate_macro_data(
                        {"market_flows": flows},
                        NEWS_TITLES,
                    )

    def test_reject_non_object_flow(self):
        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                {"market_flows": ["invalid"]},
                NEWS_TITLES,
            )

    def test_accept_three_flows(self):
        data = {
            "market_flows": [
                make_flow(),
                make_flow(
                    "금리 관련 이슈",
                    [NEWS_TITLES[2]],
                ),
                make_flow(
                    "환율 관련 이슈",
                    [NEWS_TITLES[4]],
                ),
            ]
        }

        result = macro.validate_macro_data(
            data,
            NEWS_TITLES,
        )

        self.assertEqual(
            len(result["market_flows"]),
            3,
        )

    def test_reject_more_than_three_flows(self):
        data = {
            "market_flows": [
                make_flow(flow)
                for flow in macro.FLOW_CANDIDATES[:4]
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_reject_unknown_flow(self):
        data = {
            "market_flows": [
                make_flow("허용되지 않은 시장 흐름")
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_reject_duplicate_flows(self):
        data = {
            "market_flows": [
                make_flow(),
                make_flow(),
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_reject_invalid_evidence(self):
        for evidence in ["invalid", {}, [], 123]:
            with self.subTest(evidence=evidence):
                data = {
                    "market_flows": [
                        make_flow(evidence=evidence)
                    ]
                }

                with self.assertRaises(ValueError):
                    macro.validate_macro_data(
                        data,
                        NEWS_TITLES,
                    )

    def test_accept_four_evidence_titles(self):
        data = {
            "market_flows": [
                make_flow(
                    "기타 시장 이슈",
                    NEWS_TITLES[:4],
                )
            ]
        }

        result = macro.validate_macro_data(
            data,
            NEWS_TITLES,
        )

        self.assertEqual(
            len(result["market_flows"][0]["evidence_news"]),
            4,
        )

    def test_reject_more_than_four_evidence_titles(self):
        data = {
            "market_flows": [
                make_flow(
                    evidence=NEWS_TITLES.copy(),
                )
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_reject_hallucinated_evidence(self):
        data = {
            "market_flows": [
                make_flow(evidence=["입력에 존재하지 않는 뉴스"]),
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_reject_modified_evidence(self):
        data = {
            "market_flows": [
                make_flow(evidence=[NEWS_TITLES[0] + "."]),
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_reject_non_string_evidence(self):
        for title in [None, 123, {}, []]:
            with self.subTest(title=title):
                data = {
                    "market_flows": [
                        make_flow(evidence=[title])
                    ]
                }

                with self.assertRaises(ValueError):
                    macro.validate_macro_data(
                        data,
                        NEWS_TITLES,
                    )

    def test_reject_duplicate_evidence(self):
        data = {
            "market_flows": [
                make_flow(
                    evidence=[
                        NEWS_TITLES[0],
                        NEWS_TITLES[0],
                    ],
                )
            ]
        }

        with self.assertRaises(ValueError):
            macro.validate_macro_data(
                data,
                NEWS_TITLES,
            )

    def test_extract_valid_json(self):
        data = {
            "market_flows": [make_flow()]
        }

        result = macro.extract_json(
            json.dumps(data, ensure_ascii=False)
        )

        self.assertEqual(result, data)

    def test_reject_invalid_json(self):
        for text in [
            "",
            "invalid",
            '{"market_flows":',
            "```json\n{}\n```",
            "설명문\n{}",
            "[]",
        ]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    macro.extract_json(text)

    def test_call_accepts_stop(self):
        data = {
            "market_flows": [make_flow()]
        }

        response = make_response(
            json.dumps(data, ensure_ascii=False)
        )

        with patch.object(
            macro,
            "generate_content",
            return_value=response,
        ) as mocked_call:
            result = macro.call_macro_gemini("테스트")

        self.assertEqual(result, data)
        mocked_call.assert_called_once()

        kwargs = mocked_call.call_args.kwargs

        self.assertEqual(kwargs["model"], macro.GEMINI_MODEL)
        self.assertEqual(kwargs["policy"], macro.MACRO_POLICY)
        self.assertEqual(
            kwargs["config"].response_mime_type,
            "application/json",
        )

    def test_call_rejects_abnormal_finish_reason(self):
        for reason in [
            "MAX_TOKENS",
            "SAFETY",
            "RECITATION",
            None,
        ]:
            with self.subTest(reason=reason):
                response = make_response(
                    "{}",
                    finish_reason=reason,
                )

                with patch.object(
                    macro,
                    "generate_content",
                    return_value=response,
                ):
                    with self.assertRaises(ValueError):
                        macro.call_macro_gemini("테스트")

    def test_call_rejects_missing_candidates(self):
        for response in [
            SimpleNamespace(text="{}"),
            SimpleNamespace(text="{}", candidates=[]),
        ]:
            with self.subTest(response=response):
                with patch.object(
                    macro,
                    "generate_content",
                    return_value=response,
                ):
                    with self.assertRaises(ValueError):
                        macro.call_macro_gemini("테스트")

    def test_call_rejects_empty_response(self):
        for text in [None, "", "   "]:
            with self.subTest(text=text):
                response = make_response(text)

                with patch.object(
                    macro,
                    "generate_content",
                    return_value=response,
                ):
                    with self.assertRaises(ValueError):
                        macro.call_macro_gemini("테스트")

    def test_validation_failure_returns_fallback(self):
        data = {
            "market_flows": [
                make_flow(
                    evidence=["존재하지 않는 뉴스"],
                )
            ]
        }

        with patch.object(
            macro,
            "call_macro_gemini",
            return_value=data,
        ):
            result = macro.analyze_macro_with_status(
                NEWS_DATA
            )

        self.assertEqual(result["status"], "fallback")
        self.assertIn(macro.FALLBACK_NOTICE, result["analysis"])
        self.assertIn(NEWS_TITLES[0], result["analysis"])
        self.assertNotIn(
            "존재하지 않는 뉴스",
            result["analysis"],
        )
        self.assertTrue(result["error"])

    def test_no_valid_news_skips_api(self):
        news = [
            {},
            {"title": None},
            {"title": "   "},
        ]

        with patch.object(
            macro,
            "call_macro_gemini",
        ) as mocked_call:
            result = macro.analyze_macro_with_status(news)

        mocked_call.assert_not_called()

        self.assertEqual(result["status"], "no_data")
        self.assertEqual(
            result["analysis"],
            macro.NO_DATA_NOTICE,
        )

    def test_prompt_contains_supervisor_feedback(self):
        feedback = "금리 관련 근거를 다시 확인하세요."

        prompt = macro.build_macro_prompt(
            NEWS_TITLES,
            feedback,
        )

        self.assertIn(feedback, prompt)

        for title in NEWS_TITLES:
            self.assertIn(title, prompt)

        for flow in macro.FLOW_CANDIDATES:
            self.assertIn(flow, prompt)

    def test_max_flows_no_news(self):
        self.assertEqual(macro.get_max_flows([]), 0)

    def test_max_flows_single_news(self):
        self.assertEqual(macro.get_max_flows(NEWS_TITLES[:1]), 1)

    def test_max_flows_duplicate_news(self):
        titles = [NEWS_TITLES[0]] * 3
        self.assertEqual(macro.get_max_flows(titles), 1)

    def test_max_flows_two_news(self):
        self.assertEqual(macro.get_max_flows(NEWS_TITLES[:2]), 3)

    def test_max_flows_twelve_news(self):
        titles = [f"테스트 뉴스 {index}" for index in range(12)]
        self.assertEqual(macro.get_max_flows(titles), 3)

    def test_accept_single_news_single_flow(self):
        titles = NEWS_TITLES[:1]
        data = {"market_flows": [make_flow(evidence=titles)]}
        self.assertEqual(macro.validate_macro_data(data, titles), data)

    def test_reject_single_news_two_flows(self):
        titles = NEWS_TITLES[:1]
        data = {
            "market_flows": [
                make_flow("증시 관련 이슈", titles),
                make_flow("금리 관련 이슈", titles),
            ]
        }
        with self.assertRaises(ValueError):
            macro.validate_macro_data(data, titles)

    def test_reject_single_news_three_flows(self):
        titles = NEWS_TITLES[:1]
        data = {
            "market_flows": [
                make_flow("증시 관련 이슈", titles),
                make_flow("금리 관련 이슈", titles),
                make_flow("환율 관련 이슈", titles),
            ]
        }
        with self.assertRaises(ValueError):
            macro.validate_macro_data(data, titles)

    def test_accept_shared_evidence_across_flows(self):
        titles = [NEWS_TITLES[2], NEWS_TITLES[4]]
        data = {
            "market_flows": [
                make_flow("금리 관련 이슈", [titles[0]]),
                make_flow("환율 관련 이슈", [titles[0], titles[1]]),
                make_flow("증시 관련 이슈", [titles[1]]),
            ]
        }
        self.assertEqual(macro.validate_macro_data(data, titles), data)

    def test_single_news_prompt_limit(self):
        prompt = macro.build_macro_prompt(NEWS_TITLES[:1])
        self.assertIn(
            "market_flows는 1개 이상 1개 이하로 구성하세요.",
            prompt
        )
        self.assertNotIn("시장 흐름은 최대 3개까지", prompt)
        self.assertIn(
            "입력 뉴스가 1개이므로 가장 직접적으로 관련된 시장 흐름 하나만 선택하세요.",
            prompt,
        )

    def test_multiple_news_prompt_limit(self):
        prompt = macro.build_macro_prompt(NEWS_TITLES[:2])
        self.assertIn("시장 흐름은 최대 3개까지", prompt)
        self.assertNotIn("시장 흐름은 최대 1개까지", prompt)
        self.assertNotIn("입력 뉴스가 1개이므로", prompt)

    def test_single_news_multiple_flows_fallback(self):
        titles = NEWS_TITLES[:1]
        news = [{"title": titles[0]}]
        data = {
            "market_flows": [
                make_flow("증시 관련 이슈", titles),
                make_flow("금리 관련 이슈", titles),
            ]
        }
        with patch.object(
            macro,
            "call_macro_gemini",
            return_value=data,
        ) as mocked_call:
            result = macro.analyze_macro_with_status(news)

        mocked_call.assert_called_once()
        self.assertEqual(result["status"], "fallback")
        self.assertIn(macro.FALLBACK_NOTICE, result["analysis"])
        self.assertIn(titles[0], result["analysis"])
        self.assertTrue(result["error"])


if __name__ == "__main__":
    unittest.main()
