"""
Silica EDA Platform
====================

Pydantic schemas for AI-assisted RTL failure analysis.

These schemas define the structured contract between:

    Simulator
        ↓
    Log Parser
        ↓
    Gemini Failure Analyzer
        ↓
    Verification Pipeline
        ↓
    Frontend
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Failure classification
# ============================================================================


class FailureCategory(str, Enum):
    """
    High-level classification of an RTL verification failure.
    """

    NONE = "none"

    SYNTAX = "syntax"

    COMPILATION = "compilation"

    INTERFACE = "interface"

    WIDTH = "width"

    TYPE = "type"

    RESET = "reset"

    CLOCK = "clock"

    COMBINATIONAL_LOGIC = "combinational_logic"

    SEQUENTIAL_LOGIC = "sequential_logic"

    FUNCTIONAL = "functional"

    TESTBENCH = "testbench"

    UNKNOWN = "unknown"


# ============================================================================
# Severity
# ============================================================================


class FailureSeverity(str, Enum):
    """
    Severity of the detected failure.
    """

    INFO = "info"

    WARNING = "warning"

    ERROR = "error"

    CRITICAL = "critical"


# ============================================================================
# Evidence
# ============================================================================


class FailureEvidence(BaseModel):
    """
    Concrete evidence supporting the AI diagnosis.
    """

    source: str = Field(
        ...,
        description=(
            "Evidence source, such as compiler, simulation, "
            "assertion, or testbench."
        ),
    )

    message: str = Field(
        ...,
        description="Relevant diagnostic message.",
    )

    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Relevant RTL line number if available.",
    )

    code_context: str | None = Field(
        default=None,
        description="Relevant RTL code surrounding the failure.",
    )


# ============================================================================
# Failure analysis
# ============================================================================


class FailureAnalysis(BaseModel):
    """
    Structured AI analysis of a verification failure.

    This is deliberately structured rather than returning a block of
    free-form LLM text. Structured output makes the analysis useful to
    both the frontend and the automated repair pipeline.
    """

    failed: bool = Field(
        ...,
        description="Whether the evidence indicates a real failure.",
    )

    category: FailureCategory = Field(
        ...,
        description="Primary failure category.",
    )

    severity: FailureSeverity = Field(
        ...,
        description="Failure severity.",
    )

    root_cause: str = Field(
        ...,
        min_length=1,
        max_length=5_000,
        description="Likely root cause of the failure.",
    )

    explanation: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Human-readable explanation.",
    )

    suggested_fix: str = Field(
        ...,
        min_length=1,
        max_length=5_000,
        description="Recommended correction.",
    )

    evidence: list[FailureEvidence] = Field(
        default_factory=list,
        max_length=20,
        description="Evidence supporting the diagnosis.",
    )

    affected_signals: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Signals involved in the failure.",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in the diagnosis.",
    )

    repairable: bool = Field(
        default=True,
        description=(
            "Whether the failure is suitable for automated RTL repair."
        ),
    )

    def to_dict(self) -> dict:
        """
        Return a JSON-compatible representation.
        """

        return self.model_dump(
            mode="json"
        )