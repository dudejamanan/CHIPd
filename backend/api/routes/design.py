"""
Silica EDA Platform
===================

FastAPI routes for AI-assisted hardware design.

The route layer is intentionally thin.

Business logic belongs in:
    backend/services/

The API is responsible for:
    - Request validation
    - Calling DesignService
    - Returning stable JSON responses
    - Translating application errors into HTTP errors
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.design_service import (
    DesignServiceError,
    design_service,
)
from backend.schemas.design import (
    RTLGenerationRequest,
    RTLGenerationResponse,
    TestbenchGenerationRequest,
    TestbenchGenerationResponse,
    DesignCreate,
    DesignUpdate,
    DesignResponse,
    DesignSourceResponse,
    DesignListResponse,
)

# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    tags=["Design"],
)


# ============================================================================
# Request models
# ============================================================================


class RTLGenerationRequest(BaseModel):
    """
    Request body for RTL generation.
    """

    description: str = Field(
        ...,
        min_length=3,
        max_length=20_000,
        description=(
            "Natural-language description of the desired hardware."
        ),
        examples=[
            "Create a 4-bit synchronous counter with an active-low reset."
        ],
    )


class VerificationRequest(BaseModel):
    """
    Request body for complete RTL generation + verification.
    """

    description: str = Field(
        ...,
        min_length=3,
        max_length=20_000,
        description=(
            "Natural-language hardware specification."
        ),
        examples=[
            (
                "Create a 4-bit counter with an active-low reset. "
                "The counter increments on every rising clock edge."
            )
        ],
    )


# ============================================================================
# Response models
# ============================================================================


class RTLGenerationResponse(BaseModel):
    """
    Backward-compatible lightweight RTL response.

    This is useful for the existing frontend Generate RTL button.
    """

    design_id: str | None = None

    rtl_source: str

    message: str = (
        "RTL generated successfully."
    )


class VerificationResponse(BaseModel):
    """
    Complete verification response.

    This is the richer response used by the SIH MVP.
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

    verification_history: list[
        dict[str, Any]
    ]


# ============================================================================
# Health-style design endpoint
# ============================================================================


@router.get(
    "/",
    summary="Design service status",
)
async def design_status() -> dict[str, str]:
    """
    Return basic information about the design service.
    """

    return {
        "service": "design",
        "status": "operational",
    }


# ============================================================================
# Generate RTL
# ============================================================================


@router.post(
    "/generate-rtl",
    response_model=RTLGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate RTL from a hardware description",
)
async def generate_rtl(
    request: RTLGenerationRequest,
) -> RTLGenerationResponse:
    """
    Generate SystemVerilog RTL from a natural-language specification.

    This endpoint is intentionally lightweight and exists for the
    frontend's basic RTL generation workflow.

    For the full SIH demonstration, use:

        POST /design/verify

    which additionally compiles, simulates, diagnoses and repairs
    the generated RTL.
    """

    try:

        result = (
            await design_service.generate_and_verify(
                request.description
            )
        )

    except DesignServiceError as exc:

        logger.warning(
            "Design generation failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception(
            "Unexpected RTL generation error"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred while "
                "generating RTL."
            ),
        ) from exc

    return RTLGenerationResponse(
        design_id=None,
        rtl_source=result.rtl_source,
        message=result.message,
    )


# ============================================================================
# Complete verification pipeline
# ============================================================================


@router.post(
    "/verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate, verify and repair RTL",
)
async def verify_design(
    request: VerificationRequest,
) -> VerificationResponse:
    """
    Run the complete AI-assisted EDA workflow.

    Pipeline:

        Specification
            ↓
        Gemini RTL generation
            ↓
        Gemini testbench generation
            ↓
        Icarus compilation
            ↓
        Simulation
            ↓
        Failure analysis
            ↓
        Gemini RTL repair
            ↓
        Re-verification
    """

    try:

        result = (
            design_service.generate_and_verify(
                request.description
            )
        )

    except DesignServiceError as exc:

        logger.warning(
            "Design verification request failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception(
            "Unexpected verification pipeline error"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred while "
                "running the verification pipeline."
            ),
        ) from exc

    return VerificationResponse(
        verified=result.verified,
        status=result.status,
        specification=result.specification,
        rtl_source=result.rtl_source,
        testbench_source=result.testbench_source,
        attempts=result.attempts,
        duration_ms=result.duration_ms,
        message=result.message,
        diagnostics=result.diagnostics,
        analysis=result.analysis,
        verification_history=(
            result.verification_history
        ),
    )