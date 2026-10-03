"""llm_client.py - Core API connection layer for the luxury description agent.

Deliberately free of Streamlit imports so it can be unit-tested and reused.
Requires: pip install anthropic
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5-5"


class LLMError(Exception):
    """Single exception type the UI layer needs to handle."""


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str = DEFAULT_MODEL
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: float = 30.0  # seconds
    max_retries: int = 3  # SDK retries 429/5xx/connection errors with backoff

    def __post_init__(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("API key is missing. Set ANTHROPIC_API_KEY.")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be positive.")
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("temperature must be between 0.0 and 1.0.")

    @classmethod
    def from_env(cls, **overrides) -> "LLMConfig":
        """Build config from environment variables; kwargs override defaults."""
        return cls(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
            **overrides,
        )


def create_client(config: LLMConfig) -> anthropic.Anthropic:
    """Create a reusable client. Build once and share it; do not recreate per request."""
    return anthropic.Anthropic(
        api_key=config.api_key,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )


def generate_text(
    client: anthropic.Anthropic,
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Send one request and return the generated text.

    Raises:
        LLMError: with a user-safe message for any API-level failure.
    """
    if not user_prompt or not user_prompt.strip():
        raise ValueError("user_prompt must not be empty.")

    try:
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.AuthenticationError as exc:
        raise LLMError("Authentication failed. Check your API key.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMError("Rate limit reached. Please try again shortly.") from exc
    except anthropic.APITimeoutError as exc:
        raise LLMError("The request timed out. Please try again.") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError("Could not reach the API. Check your connection.") from exc
    except anthropic.APIStatusError as exc:
        logger.error("API error %s: %s", exc.status_code, exc.message)
        raise LLMError(f"The API returned an error (HTTP {exc.status_code}).") from exc

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise LLMError("The model returned an empty response.")

    if response.stop_reason == "max_tokens":
        logger.warning("Output truncated at max_tokens=%d", config.max_tokens)

    return text


if __name__ == "__main__":
    # Smoke test: ANTHROPIC_API_KEY=... python llm_client.py
    logging.basicConfig(level=logging.INFO)
    cfg = LLMConfig.from_env(max_tokens=200)
    print(
        generate_text(
            create_client(cfg),
            cfg,
            system_prompt="You are a luxury copywriter.",
            user_prompt="Write one sentence about a hand-stitched leather weekender bag.",
        )
    )