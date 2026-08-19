"""
Silica EDA Platform
===================

Application service for hardware design workflows.

This layer sits between FastAPI routes and the lower-level services.

Responsibilities
----------------
- Validate design requests
- Run the verification pipeline
- Expose a clean application-level API
- Keep FastAPI routes thin
- Prepare data for persistence/API responses

This service deliberately does not contain HTTP-specific logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.services.verification_pipeline import (
    PipelineStatus,
    VerificationPipelineError,
    VerificationPipelineResult,
    verification_pipeline,
)


# ============================================================================
# Exceptions
# ============================================================================


class DesignServiceError(Exception):
    """Base exception for design-service failures."""


# ============================================================================
# Design generation result
# ============================================================================


@dataclass(slots=True)
class DesignWorkflowResult:
    """
    Clean application-level result returned to the API layer.
    """

    verified: bool

    status: str

    specification: str

    rtl_source: str

    testbench_source: str

    attempts: int

    duration_ms: int

    message: str

    diagnostics: dict[str, Any] | None

    analysis: dict[str, Any] | None

    verification_history: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert result into JSON-compatible data."""

        return {
            "verified": self.verified,
            "status": self.status,
            "specification": self.specification,
            "rtl_source": self.rtl_source,
            "testbench_source": self.testbench_source,
            "attempts": self.attempts,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "diagnostics": self.diagnostics,
            "analysis": self.analysis,
            "verification_history": self.verification_history,
        }


# ============================================================================
# Design Service
# ============================================================================


class DesignService:
    """
    High-level service for AI-assisted chip design workflows.
    """

    # ------------------------------------------------------------------------
    # Generate + verify
    # ------------------------------------------------------------------------

    async def generate_and_verify(
        self,
        specification: str,
    ) -> DesignWorkflowResult:
        """
        Generate RTL from a hardware specification and verify it.

        The workflow may automatically repair failed RTL within the
        configured repair budget.
        """

        specification = self._normalize_specification(
            specification
        )

        try:

            pipeline_result = (
                await verification_pipeline.run(
                    specification
                )
            )

        except VerificationPipelineError as exc:

            raise DesignServiceError(
                str(exc)
            ) from exc

        return self._convert_pipeline_result(
            pipeline_result
        )

    # ------------------------------------------------------------------------
    # Pipeline → application result
    # ------------------------------------------------------------------------

    def _convert_pipeline_result(
        self,
        result: VerificationPipelineResult,
    ) -> DesignWorkflowResult:
        """
        Convert internal pipeline result into a stable API-facing result.
        """

        diagnostics = None

        if result.final_diagnostics is not None:

            diagnostics = (
                result.final_diagnostics.to_dict()
            )

        analysis = None

        if result.final_analysis is not None:

            analysis = (
                result.final_analysis.to_dict()
            )

        history: list[
            dict[str, Any]
        ] = []

        for attempt in result.attempts:

            attempt_data = (
                attempt.to_dict()
            )

            # ---------------------------------------------------------------
            # The frontend needs the metadata and diagnostics for each
            # attempt, but does not need duplicated complete source code
            # everywhere in the history.
            # ---------------------------------------------------------------

            history.append(
                {
                    "attempt_number": (
                        attempt_data[
                            "attempt_number"
                        ]
                    ),
                    "status": (
                        attempt_data[
                            "status"
                        ]
                    ),
                    "passed": (
                        attempt_data[
                            "passed"
                        ]
                    ),
                    "compile_success": (
                        attempt_data[
                            "compile_success"
                        ]
                    ),
                    "simulation_success": (
                        attempt_data[
                            "simulation_success"
                        ]
                    ),
                    "duration_ms": (
                        attempt_data[
                            "duration_ms"
                        ]
                    ),
                    "diagnostics": (
                        attempt_data[
                            "diagnostics"
                        ]
                    ),
                    "failure_analysis": (
                        attempt_data[
                            "failure_analysis"
                        ]
                    ),
                    "repair": (
                        attempt_data[
                            "repair"
                        ]
                    ),
                }
            )

        return DesignWorkflowResult(
            verified=result.verified,
            status=result.status.value,
            specification=result.specification,
            rtl_source=result.rtl_source,
            testbench_source=result.testbench_source,
            attempts=result.total_attempts,
            duration_ms=result.total_duration_ms,
            message=result.final_message,
            diagnostics=diagnostics,
            analysis=analysis,
            verification_history=history,
        )

    # ------------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------------

    def _normalize_specification(
        self,
        specification: str,
    ) -> str:
        """
        Normalize and validate the hardware specification.
        """

        if specification is None:

            raise DesignServiceError(
                "Hardware specification is required."
            )

        specification = specification.strip()

        if not specification:

            raise DesignServiceError(
                "Hardware specification cannot be empty."
            )

        # Keep this limit intentionally generous for the MVP while
        # protecting the Gemini API from accidental enormous payloads.
        if len(specification) > 20_000:

            raise DesignServiceError(
                "Hardware specification is too long. "
                "Please keep it below 20,000 characters."
            )

        return specification


# ============================================================================
# Shared service instance
# ============================================================================

design_service = DesignService()