from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.design_service import DesignServiceError, design_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Design"])


class RTLGenerationRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=20_000)


class VerificationRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=20_000)


class RTLGenerationResponse(BaseModel):
    design_id: str | None = None
    rtl_source: str
    testbench_source: str = ""
    verified: bool = False
    status: str = "unknown"
    attempts: int = 0
    duration_ms: int = 0
    message: str = "RTL generated successfully."
    diagnostics: dict[str, Any] | None = None
    analysis: dict[str, Any] | None = None
    verification_history: list[dict[str, Any]] = []


class VerificationResponse(BaseModel):
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


@router.get("/", summary="Design service status")
async def design_status() -> dict[str, str]:
    return {"service": "design", "status": "operational"}


@router.post("/generate-rtl", response_model=RTLGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_rtl(request: RTLGenerationRequest) -> RTLGenerationResponse:
    try:
        result = await design_service.generate_and_verify(request.description)
    except DesignServiceError as exc:
        logger.warning("Design generation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected RTL generation error")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while generating RTL: {exc}",
        ) from exc

    return RTLGenerationResponse(
        design_id=None,
        rtl_source=result.rtl_source,
        testbench_source=result.testbench_source,
        verified=result.verified,
        status=result.status,
        attempts=result.attempts,
        duration_ms=result.duration_ms,
        message=result.message,
        diagnostics=result.diagnostics,
        analysis=result.analysis,
        verification_history=result.verification_history,
    )


@router.post("/verify", response_model=VerificationResponse, status_code=status.HTTP_200_OK)
async def verify_design(request: VerificationRequest) -> VerificationResponse:
    try:
        result = await design_service.generate_and_verify(request.description)
    except DesignServiceError as exc:
        logger.warning("Design verification request failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected verification pipeline error")
        raise HTTPException(status_code=500, detail=f"Verification failed: {exc}") from exc

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
        verification_history=result.verification_history,
    )