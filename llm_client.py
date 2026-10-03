"""llm_client.py - Core Google Gemini API layer for Maison Copy.

Deliberately free of Streamlit imports so it can be unit-tested and reused.
Requires: pip install -U google-genai python-dotenv
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import httpx  # installed as a dependency of google-genai
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

logger = logging.getLogger(__name__)

# Google retires Gemini model IDs regularly (gemini-1.5-* is long gone and
# gemini-2.5-* is scheduled for shutdown in October 2026), so the model is
# configurable via the GEMINI_MODEL env var or the app's sidebar.
DEFAULT_MODEL = "gemini-3.5-flash"

# The .env file lives next to this module (your luxury_ai folder), so the key is found
# no matter which directory `streamlit run` is started from.
ENV_FILE = Path(__file__).resolve().parent / ".env"
API_KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


def load_env_file() -> None:
    """Load variables from the .env file, if present.

    Real environment variables win over the file (override=False). The utf-8-sig
    encoding tolerates the byte-order mark that some Windows editors add.
    """
    load_dotenv(ENV_FILE, override=False, encoding="utf-8-sig")


def get_env_api_key() -> str:
    """Return the key from the .env file or the environment, or "" if none is set."""
    load_env_file()
    for name in API_KEY_VARS:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


class LLMError(Exception):
    """Single exception type the UI layer needs to handle."""


@dataclass(frozen=True)
class LLMConfig:
    api_key: str = field(repr=False)  # repr=False keeps the key out of logs and tracebacks
    model: str = DEFAULT_MODEL
    max_output_tokens: int = 2048  # includes the model's internal "thinking" tokens
    temperature: float | None = None  # None = model default (recommended for Gemini 3.x)
    timeout: float = 60.0  # seconds
    max_retries: int = 2  # transient failures only (429, 5xx, network)

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("API key is missing. Provide a Google Gemini API key.")
        if not self.model or not self.model.strip():
            raise ValueError("Model name must not be empty.")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive.")
        if self.temperature is not None and not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0.")

    @classmethod
    def from_env(cls, **overrides) -> "LLMConfig":
        """Build config from environment variables; kwargs override defaults."""
        api_key = get_env_api_key()
        return cls(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            **overrides,
        )


# --------------------------------------------------------------------------- #
# Client and request construction
# --------------------------------------------------------------------------- #


def create_client(config: LLMConfig) -> genai.Client:
    """Create a Gemini client. Cheap to build, so no shared cache of secrets is needed."""
    return genai.Client(
        api_key=config.api_key,
        http_options=types.HttpOptions(timeout=int(config.timeout * 1000)),  # milliseconds
    )


def _thinking_config(model: str) -> types.ThinkingConfig | None:
    """Keep reasoning light so the token budget goes to the copy, not to hidden thoughts."""
    name = model.lower().removeprefix("models/")
    if name.startswith("gemini-3"):
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
    if name.startswith("gemini-2.5-flash"):
        return types.ThinkingConfig(thinking_budget=0)
    return None


def _build_config(config: LLMConfig, system_prompt: str) -> types.GenerateContentConfig:
    kwargs: dict = {
        "system_instruction": system_prompt,
        "max_output_tokens": config.max_output_tokens,
    }
    if config.temperature is not None:
        kwargs["temperature"] = config.temperature
    thinking = _thinking_config(config.model)
    if thinking is not None:
        kwargs["thinking_config"] = thinking
    return types.GenerateContentConfig(**kwargs)


# --------------------------------------------------------------------------- #
# Error handling
# --------------------------------------------------------------------------- #


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    code = getattr(exc, "code", None)
    return isinstance(exc, errors.APIError) and (code == 429 or (code or 0) >= 500)


def _translate(exc: Exception) -> LLMError:
    """Map SDK and network exceptions to short, user-safe messages."""
    if isinstance(exc, httpx.TimeoutException):
        return LLMError("The request timed out. Please try again.")
    if isinstance(exc, httpx.TransportError):
        return LLMError("Could not reach the Gemini API. Check your connection.")

    code = getattr(exc, "code", None)
    message = (getattr(exc, "message", "") or str(exc)).lower()

    if code == 429:
        return LLMError("Quota or rate limit reached. Wait a minute and try again.")
    if code == 404:
        return LLMError("This model is unavailable or has been retired. Choose another one under Advanced.")
    if code in (401, 403) or "api key" in message:
        return LLMError("Authentication failed. Check your Gemini API key.")
    if code is not None and code >= 500:
        return LLMError("Gemini is temporarily unavailable. Please try again shortly.")

    logger.error("Gemini API error %s: %s", code, message)
    return LLMError(f"The API rejected the request (HTTP {code}).")


def _require_prompt(user_prompt: str) -> None:
    if not user_prompt or not user_prompt.strip():
        raise ValueError("user_prompt must not be empty.")


_EMPTY_MESSAGE = "The model returned an empty response (it may have been blocked by safety filters)."


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def generate_text(
    client: genai.Client,
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Send one request and return the generated text.

    Raises:
        LLMError: with a user-safe message for any API-level failure.
    """
    _require_prompt(user_prompt)
    request = {
        "model": config.model,
        "contents": user_prompt,
        "config": _build_config(config, system_prompt),
    }

    for attempt in range(config.max_retries + 1):
        try:
            response = client.models.generate_content(**request)
            break
        except (errors.APIError, httpx.TransportError) as exc:
            if attempt < config.max_retries and _is_retryable(exc):
                delay = 2.0**attempt
                logger.warning("Transient error (%s). Retrying in %.0fs.", exc, delay)
                time.sleep(delay)
                continue
            raise _translate(exc) from exc

    text = (response.text or "").strip()
    if not text:
        raise LLMError(_EMPTY_MESSAGE)

    candidates = response.candidates or []
    if candidates and getattr(candidates[0].finish_reason, "name", "") == "MAX_TOKENS":
        logger.warning("Output truncated at max_output_tokens=%d", config.max_output_tokens)

    return text


def stream_text(
    client: genai.Client,
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> Iterator[str]:
    """Yield the response in chunks as it is generated (for live display).

    Raises:
        LLMError: with a user-safe message for any API-level failure.
    """
    _require_prompt(user_prompt)
    emitted = False
    try:
        for chunk in client.models.generate_content_stream(
            model=config.model,
            contents=user_prompt,
            config=_build_config(config, system_prompt),
        ):
            if chunk.text:
                emitted = True
                yield chunk.text
    except (errors.APIError, httpx.TransportError) as exc:
        raise _translate(exc) from exc

    if not emitted:
        raise LLMError(_EMPTY_MESSAGE)


if __name__ == "__main__":
    # Smoke test: GEMINI_API_KEY=... python llm_client.py
    logging.basicConfig(level=logging.INFO)
    cfg = LLMConfig.from_env()
    print(
        generate_text(
            create_client(cfg),
            cfg,
            system_prompt="You are a luxury copywriter.",
            user_prompt="Write one sentence about a hand-stitched leather weekender bag.",
        )
    )