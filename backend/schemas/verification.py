"""
Silica EDA Platform
====================

Pydantic schemas for RTL generation, compilation, simulation and
verification results.

These schemas form the stable API contract consumed by the frontend.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from backend.schemas.analysis import (
    FailureAnalysis,
)


# ============================================================================
# Verification status
# ============================================================================


class VerificationStatus(str, Enum):
    """
    State of a hardware verification workflow.
    """

    PENDING = "pending"

    GENERATING = "generating"

    COMPILING = "compiling"

    SIMULATING = "simulating"

    ANALYZING = "analyzing"

    REPAIRING = "repairing"

    REVERIFYING = "reverifying"

    VERIFIED = "verified"

    FAILED = "failed"

    ERROR = "error"


# ============================================================================
# Diagnostic
# ============================================================================


class Diagnostic(BaseModel):
    """
    Individual compiler or simulator diagnostic.
    """

    severity: str = Field(
        ...,
        description="Diagnostic severity.",
    )

    message: str = Field(
        ...,
        description="Diagnostic message.",
    )

    source: str | None = Field(
        default=None,
        description="Diagnostic source.",
    )

    line_number: int | None = Field(
        default=None,
        ge=1,
        description="RTL line number.",
    )

    column_number: int | None = Field(
        default=None,
        ge=1,
        description="Column number.",
    )

    code_context: str | None = Field(
        default=None,
        description="Relevant source code.",
    )


# ============================================================================
# Diagnostic report
# ============================================================================


class DiagnosticReport(BaseModel):
    """
    Aggregated compiler/simulation diagnostics.
    """

    success: bool = Field(
        ...,
        description="Whether diagnostics indicate successful verification.",
    )

    compile_success: bool = Field(
        default=False,
    )

    simulation_success: bool = Field(
        default=False,
    )

    errors: list[Diagnostic] = Field(
        default_factory=list,
    )

    warnings: list[Diagnostic] = Field(
        default_factory=list,
    )

    info: list[Diagnostic] = Field(
        default_factory=list,
    )

    raw_output: str = Field(
        default="",
        description="Raw compiler/simulator output.",
    )


# ============================================================================
# Repair result
# ============================================================================


class RepairResult(BaseModel):
    """
    AI-generated RTL repair candidate.
    """

    rtl_source: str = Field(
        ...,
        min_length=1,
    )

    explanation: str = Field(
        ...,
        min_length=1,
    )

    changes: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    preserved_interface: bool = True

    repair_scope: str = "minimal"


# ============================================================================
# Verification attempt
# ============================================================================


class VerificationAttempt(BaseModel):
    """
    One compile/simulation attempt.
    """

    attempt_number: int = Field(
        ...,
        ge=1,
    )

    status: VerificationStatus

    passed: bool

    compile_success: bool

    simulation_success: bool

    duration_ms: int = Field(
        ...,
        ge=0,
    )

    diagnostics: DiagnosticReport | None = None

    failure_analysis: FailureAnalysis | None = None

    repair: RepairResult | None = None


# ============================================================================
# Verification request
# ============================================================================


class VerificationRequest(BaseModel):
    """
    Request sent by the frontend to begin a verification workflow.
    """

    description: str = Field(
        ...,
        min_length=3,
        max_length=20_000,
        description=(
            "Natural-language description of the desired hardware."
        ),
        examples=[
            (
                "Create a 4-bit counter with an active-low reset. "
                "The counter increments on every rising edge of clk."
            )
        ],
    )

    project_id: str | None = Field(
        default=None,
        description=(
            "Optional project ID to associate with this design."
        ),
    )

    auto_repair: bool = Field(
        default=True,
        description=(
            "Whether the system should automatically attempt "
            "AI-assisted RTL repair after a verification failure."
        ),
    )


# ============================================================================
# RTL generation request
# ============================================================================


class RTLGenerationRequest(BaseModel):
    """
    Request for RTL generation.
    """

    description: str = Field(
        ...,
        min_length=3,
        max_length=20_000,
    )

    project_id: str | None = None


# ============================================================================
# RTL generation response
# ============================================================================


class RTLGenerationResponse(BaseModel):
    """
    Response containing generated RTL.
    """

    design_id: str | None = None

    rtl_source: str

    message: str

    model: str | None = None


# ============================================================================
# Complete verification response
# ============================================================================


class VerificationResponse(BaseModel):
    """
    Complete result returned to the frontend.
    """

    verified: bool

    status: VerificationStatus

    specification: str

    rtl_source: str

    testbench_source: str

    attempts: int = Field(
        ...,
        ge=0,
    )

    duration_ms: int = Field(
        ...,
        ge=0,
    )

    message: str

    diagnostics: DiagnosticReport | None = None

    analysis: FailureAnalysis | None = None

    verification_history: list[
        VerificationAttempt
    ] = Field(
        default_factory=list
    )

    project_id: str | None = None