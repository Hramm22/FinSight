
import unittest
from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai import types

from app.utils.gemini_client import (
    GeminiPolicy,
    create_gemini_client,
    generate_content,
    get_error_status,
    log_response_metrics,
)


MODULE = "app.utils.gemini_client"


class FakeAPIError(Exception):
    def __init__(self, code):
        super().__init__(f"API error: {code}")
        self.code = code


class GeminiPolicyTests(unittest.TestCase):
    def test_default_policy(self):
        policy = GeminiPolicy()

        self.assertEqual(policy.timeout_ms, 30000)
        self.assertEqual(policy.max_retries, 1)
        self.assertEqual(policy.retry_delay_seconds, 1.0)

    def test_invalid_timeout(self):
        with self.assertRaises(ValueError):
            GeminiPolicy(timeout_ms=9999)

    def test_invalid_max_retries(self):
        with self.assertRaises(ValueError):
            GeminiPolicy(max_retries=-1)

    def test_invalid_retry_delay(self):
        with self.assertRaises(ValueError):
            GeminiPolicy(retry_delay_seconds=-1)

    def test_policy_is_immutable(self):
        policy = GeminiPolicy()

        with self.assertRaises(FrozenInstanceError):
            policy.timeout_ms = 60000


class ErrorStatusTests(unittest.TestCase):
    def test_code_attribute(self):
        self.assertEqual(
            get_error_status(FakeAPIError(503)),
            503,
        )

    def test_status_code_attribute(self):
        error = RuntimeError("API error")
        error.status_code = 429

        self.assertEqual(get_error_status(error), 429)

    def test_string_status(self):
        self.assertEqual(
            get_error_status(FakeAPIError("500")),
            500,
        )

    def test_missing_status(self):
        self.assertIsNone(
            get_error_status(TimeoutError("Timeout"))
        )

    def test_invalid_status(self):
        self.assertIsNone(
            get_error_status(FakeAPIError("invalid"))
        )


class ClientCreationTests(unittest.TestCase):
    def test_missing_api_key(self):
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": ""},
        ):
            with patch(f"{MODULE}.genai.Client") as constructor:
                with self.assertRaises(RuntimeError):
                    create_gemini_client(GeminiPolicy())

                constructor.assert_not_called()

    def test_client_configuration(self):
        policy = GeminiPolicy(timeout_ms=45000)

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-api-key"},
        ):
            with patch(f"{MODULE}.genai.Client") as constructor:
                result = create_gemini_client(policy)

                self.assertIs(result, constructor.return_value)
                constructor.assert_called_once()

                kwargs = constructor.call_args.kwargs

                self.assertEqual(
                    kwargs["api_key"],
                    "test-api-key",
                )

                self.assertEqual(
                    kwargs["http_options"].timeout,
                    45000,
                )

                self.assertEqual(
                    kwargs["http_options"].retry_options.attempts,
                    1,
                )


class GenerateContentTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()

        self.response = SimpleNamespace(
            text="test response",
            usage_metadata=SimpleNamespace(
                prompt_token_count=100,
                candidates_token_count=20,
                thoughts_token_count=30,
                total_token_count=150,
            ),
        )

        self.config = types.GenerateContentConfig(
            temperature=0.1,
        )

        self.policy = GeminiPolicy(
            timeout_ms=30000,
            max_retries=1,
            retry_delay_seconds=1.0,
        )

        self.client_patcher = patch(
            f"{MODULE}.create_gemini_client",
            return_value=self.client,
        )

        self.sleep_patcher = patch(
            f"{MODULE}.time.sleep",
        )

        self.mock_create_client = self.client_patcher.start()
        self.mock_sleep = self.sleep_patcher.start()

        self.addCleanup(self.client_patcher.stop)
        self.addCleanup(self.sleep_patcher.stop)

    def call_generate(self, policy=None):
        return generate_content(
            agent_name="Test",
            model="test-model",
            prompt="test prompt",
            config=self.config,
            policy=policy if policy is not None else self.policy,
        )

    def test_success(self):
        self.client.models.generate_content.return_value = (
            self.response
        )

        result = self.call_generate()

        self.assertIs(result, self.response)

        self.mock_create_client.assert_called_once_with(
            self.policy
        )

        self.client.models.generate_content.assert_called_once_with(
            model="test-model",
            contents="test prompt",
            config=self.config,
        )

        self.mock_sleep.assert_not_called()
        self.client.close.assert_called_once_with()

    def test_retry_on_429(self):
        self.client.models.generate_content.side_effect = [
            FakeAPIError(429),
            self.response,
        ]

        result = self.call_generate()

        self.assertIs(result, self.response)
        self.assertEqual(
            self.client.models.generate_content.call_count,
            2,
        )
        self.mock_sleep.assert_called_once_with(1.0)
        self.client.close.assert_called_once_with()

    def test_retry_on_503(self):
        self.client.models.generate_content.side_effect = [
            FakeAPIError(503),
            self.response,
        ]

        result = self.call_generate()

        self.assertIs(result, self.response)
        self.assertEqual(
            self.client.models.generate_content.call_count,
            2,
        )
        self.mock_sleep.assert_called_once_with(1.0)
        self.client.close.assert_called_once_with()

    def test_non_retryable_400(self):
        error = FakeAPIError(400)

        self.client.models.generate_content.side_effect = error

        with self.assertRaises(FakeAPIError) as caught:
            self.call_generate()

        self.assertIs(caught.exception, error)
        self.client.models.generate_content.assert_called_once()
        self.mock_sleep.assert_not_called()
        self.client.close.assert_called_once_with()

    def test_non_retryable_401(self):
        self.client.models.generate_content.side_effect = (
            FakeAPIError(401)
        )

        with self.assertRaises(FakeAPIError):
            self.call_generate()

        self.client.models.generate_content.assert_called_once()
        self.mock_sleep.assert_not_called()
        self.client.close.assert_called_once_with()

    def test_retry_limit_exceeded(self):
        self.client.models.generate_content.side_effect = [
            FakeAPIError(503),
            FakeAPIError(503),
        ]

        with self.assertRaises(FakeAPIError):
            self.call_generate()

        self.assertEqual(
            self.client.models.generate_content.call_count,
            2,
        )
        self.mock_sleep.assert_called_once_with(1.0)
        self.client.close.assert_called_once_with()

    def test_timeout_without_status(self):
        self.client.models.generate_content.side_effect = (
            TimeoutError("Request timed out")
        )

        with self.assertRaises(TimeoutError):
            self.call_generate()

        self.client.models.generate_content.assert_called_once()
        self.mock_sleep.assert_not_called()
        self.client.close.assert_called_once_with()

    def test_zero_retries(self):
        policy = GeminiPolicy(max_retries=0)

        self.client.models.generate_content.side_effect = (
            FakeAPIError(503)
        )

        with self.assertRaises(FakeAPIError):
            self.call_generate(policy)

        self.client.models.generate_content.assert_called_once()
        self.mock_sleep.assert_not_called()
        self.client.close.assert_called_once_with()

    def test_linear_retry_delay(self):
        policy = GeminiPolicy(
            max_retries=2,
            retry_delay_seconds=1.0,
        )

        self.client.models.generate_content.side_effect = [
            FakeAPIError(500),
            FakeAPIError(502),
            self.response,
        ]

        result = self.call_generate(policy)

        self.assertIs(result, self.response)
        self.assertEqual(
            self.client.models.generate_content.call_count,
            3,
        )

        delays = [
            item.args[0]
            for item in self.mock_sleep.call_args_list
        ]

        self.assertEqual(delays, [1.0, 2.0])
        self.client.close.assert_called_once_with()

    def test_close_failure_preserves_response(self):
        self.client.models.generate_content.return_value = (
            self.response
        )

        self.client.close.side_effect = RuntimeError(
            "Close failed"
        )

        with self.assertLogs(MODULE, level="WARNING") as logs:
            result = self.call_generate()

        self.assertIs(result, self.response)
        self.client.close.assert_called_once_with()

        self.assertTrue(
            any(
                "Client close failed" in message
                for message in logs.output
            )
        )


class MetricsTests(unittest.TestCase):
    def test_metrics_logging(self):
        response = SimpleNamespace(
            usage_metadata=SimpleNamespace(
                prompt_token_count=100,
                candidates_token_count=20,
                thoughts_token_count=30,
                total_token_count=150,
            )
        )

        with self.assertLogs(MODULE, level="INFO") as logs:
            log_response_metrics(
                agent_name="Test",
                model="test-model",
                response=response,
                elapsed=1.25,
                attempt=1,
            )

        output = " ".join(logs.output)

        for expected in (
            "agent=Test",
            "model=test-model",
            "attempt=1",
            "elapsed=1.25s",
            "prompt_tokens=100",
            "output_tokens=20",
            "thinking_tokens=30",
            "total_tokens=150",
        ):
            self.assertIn(expected, output)

    def test_missing_usage_metadata(self):
        response = SimpleNamespace()

        with self.assertLogs(MODULE, level="INFO") as logs:
            log_response_metrics(
                agent_name="Test",
                model="test-model",
                response=response,
                elapsed=1.0,
                attempt=1,
            )

        output = " ".join(logs.output)

        for expected in (
            "prompt_tokens=None",
            "output_tokens=None",
            "thinking_tokens=None",
            "total_tokens=None",
        ):
            self.assertIn(expected, output)


if __name__ == "__main__":
    unittest.main()