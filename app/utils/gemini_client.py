import logging
import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


@dataclass(frozen=True)
class GeminiPolicy:
    timeout_ms: int = 30000
    max_retries: int = 1
    retry_delay_seconds: float = 1.0

    def __post_init__(self):
        if self.timeout_ms < 10000:
            raise ValueError("Gemini timeout은 10000ms 이상이어야 합니다.")
        if self.max_retries < 0:
            raise ValueError("max_retries는 0 이상이어야 합니다.")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds는 0 이상이어야 합니다.")


def get_error_status(error: Exception) -> int | None:
    status = getattr(error, "code", None)

    if status is None:
        status = getattr(error, "status_code", None)

    try:
        return int(status)
    except (TypeError, ValueError):
        return None


def create_gemini_client(policy: GeminiPolicy) -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=policy.timeout_ms,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def log_response_metrics(
    agent_name: str,
    model: str,
    response,
    elapsed: float,
    attempt: int,
) -> None:
    usage = getattr(response, "usage_metadata", None)

    logger.info(
        "[GEMINI] agent=%s model=%s attempt=%s "
        "elapsed=%.2fs prompt_tokens=%s output_tokens=%s "
        "thinking_tokens=%s total_tokens=%s",
        agent_name,
        model,
        attempt,
        elapsed,
        getattr(usage, "prompt_token_count", None),
        getattr(usage, "candidates_token_count", None),
        getattr(usage, "thoughts_token_count", None),
        getattr(usage, "total_token_count", None),
    )


def generate_content(
    agent_name: str,
    model: str,
    prompt: str,
    config: types.GenerateContentConfig,
    policy: GeminiPolicy,
):
    client = create_gemini_client(policy)
    total_start = time.perf_counter()

    try:
        for retry in range(policy.max_retries + 1):
            attempt = retry + 1
            request_start = time.perf_counter()

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )

                elapsed = time.perf_counter() - request_start

                log_response_metrics(
                    agent_name,
                    model,
                    response,
                    elapsed,
                    attempt,
                )

                return response

            except Exception as error:
                status = get_error_status(error)
                elapsed = time.perf_counter() - request_start

                logger.warning(
                    "[GEMINI] agent=%s model=%s attempt=%s "
                    "elapsed=%.2fs status=%s error=%s",
                    agent_name,
                    model,
                    attempt,
                    elapsed,
                    status,
                    type(error).__name__,
                )

                if (
                    status not in RETRYABLE_STATUS_CODES
                    or retry >= policy.max_retries
                ):
                    raise

                time.sleep(policy.retry_delay_seconds * attempt)

        raise RuntimeError("Gemini API 재시도 한도 초과")

    finally:
        try:
            client.close()
        except Exception as error:
            logger.warning(
                "[GEMINI] Client close failed: %s",
                type(error).__name__,
            )

        logger.info(
            "[GEMINI] agent=%s total_elapsed=%.2fs",
            agent_name,
            time.perf_counter() - total_start,
        )