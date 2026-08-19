"""
Silica EDA Platform
===================

Central LLM service.

All AI-powered services communicate with the configured LLM
through this class.

Current provider:
    Groq

Current model:
    openai/gpt-oss-20b
"""

from __future__ import annotations

import asyncio
import logging

from groq import Groq

from backend.config import settings


logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class LLMServiceError(Exception):
    """Base exception for LLM service failures."""


class LLMError(LLMServiceError):
    """Backwards-compatible general LLM error."""


class LLMConfigurationError(LLMServiceError):
    """Raised when the LLM is not configured correctly."""


class LLMGenerationError(LLMServiceError):
    """Raised when LLM generation fails."""


# ============================================================================
# LLM Service
# ============================================================================


class LLMService:
    """
    Centralized asynchronous Groq client.

    The Groq Python SDK is synchronous, so API calls are executed
    in a worker thread to avoid blocking FastAPI's event loop.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:

        self.api_key = (
            api_key
            if api_key is not None
            else settings.groq_api_key
        )

        self.model = (
            model
            if model is not None
            else settings.groq_model
        )

        if not self.api_key:
            raise LLMConfigurationError(
                "Groq API key is not configured. "
                "Set GROQ_API_KEY in the .env file."
            )

        if not self.model:
            raise LLMConfigurationError(
                "Groq model is not configured. "
                "Set GROQ_MODEL in the .env file."
            )

        try:

            self.client = Groq(
                api_key=self.api_key
            )

            logger.info(
                "LLM service initialized. Provider=Groq Model=%s",
                self.model,
            )

        except Exception as exc:

            logger.exception(
                "Failed to initialize Groq client."
            )

            raise LLMConfigurationError(
                "Failed to initialize Groq client."
            ) from exc

    # ========================================================================
    # Public generation API
    # ========================================================================

    async def generate(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        """
        Generate text using Groq.

        Supports both:

            await llm_service.generate(
                prompt="..."
            )

        and:

            await llm_service.generate(
                system_prompt="...",
                user_prompt="...",
            )

        This keeps existing AI services compatible.
        """

        # --------------------------------------------------------------------
        # Build messages
        # --------------------------------------------------------------------

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        if user_prompt:
            messages.append(
                {
                    "role": "user",
                    "content": user_prompt.strip(),
                }
            )

        elif prompt:
            messages.append(
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            )

        if not messages:
            raise ValueError(
                "LLM prompt cannot be empty."
            )

        # --------------------------------------------------------------------
        # Configuration
        # --------------------------------------------------------------------

        temperature = (
            settings.llm_temperature
            if temperature is None
            else temperature
        )

        max_output_tokens = (
            settings.llm_max_output_tokens
            if max_output_tokens is None
            else max_output_tokens
        )

        # --------------------------------------------------------------------
        # Generate
        # --------------------------------------------------------------------

        try:

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_sync,
                    messages,
                    temperature,
                    max_output_tokens,
                    reasoning_effort,
                ),
                timeout=settings.llm_timeout_seconds,
            )

        except asyncio.TimeoutError as exc:

            logger.error(
                "Groq request timed out after %s seconds.",
                settings.llm_timeout_seconds,
            )

            raise LLMGenerationError(
                "Groq request timed out."
            ) from exc

        except LLMGenerationError:
            raise

        except Exception as exc:

            logger.exception(
                "Groq generation failed."
            )

            raise LLMGenerationError(
                f"Groq generation failed: {exc}"
            ) from exc

        # --------------------------------------------------------------------
        # Validate result
        # --------------------------------------------------------------------

        if not isinstance(response, str):

            raise LLMGenerationError(
                "Groq returned an invalid response type."
            )

        response = response.strip()

        if not response:

            raise LLMGenerationError(
                "Groq returned an empty response."
            )

        return response

    # ========================================================================
    # Synchronous Groq call
    # ========================================================================

    def _generate_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_output_tokens: int,
        reasoning_effort: str | None = None,

    ) -> str:
        """
        Execute the Groq API request synchronously.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_output_tokens,
        )

        if not response.choices:

            raise LLMGenerationError(
                "Groq returned no choices."
            )

        choice = response.choices[0]
        message = choice.message

        finish_reason = choice.finish_reason
        content = message.content

        logger.info(
            "Groq response: finish_reason=%s content_present=%s",
            finish_reason,
            bool(content),
        )

        if finish_reason == "length" and not content:
            raise LLMGenerationError(
                "Groq generation reached the output limit before "
                "returning a complete response."
            )

        if not content:
            raise LLMGenerationError(
                f"Groq returned no text. finish_reason={finish_reason}"
            )

        return content.strip()
    # ========================================================================
    # Health check
    # ========================================================================

    async def health_check(self) -> bool:
        """
        Check whether the Groq client is configured.

        Does not make an API request.
        """

        return bool(
            self.api_key
            and self.model
            and self.client
        )


# ============================================================================
# Shared singleton
# ============================================================================


llm_service = LLMService()


# ============================================================================
# Backwards compatibility
# ============================================================================

# Existing code should import:
#
#     from backend.services.llm_service import llm_service
#
# Keep these aliases so any older imports don't immediately break.

GeminiService = LLMService

gemini_service = llm_service