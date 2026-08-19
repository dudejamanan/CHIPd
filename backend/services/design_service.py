from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.services.verification_pipeline import (
    VerificationPipelineError,
    VerificationPipelineResult,
    verification_pipeline,
)


class DesignServiceError(Exception):
    """Base exception for design-service failures."""


@dataclass(slots=True)
class DesignWorkflowResult:
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


class DesignService:
    async def generate_and_verify(self, specification: str) -> DesignWorkflowResult:
        specification = self._normalize_specification(specification)
        try:
            result = await verification_pipeline.run(specification)
        except VerificationPipelineError as exc:
            raise DesignServiceError(str(exc)) from exc
        return self._convert_pipeline_result(result)

    def _convert_pipeline_result(
        self,
        result: VerificationPipelineResult,
    ) -> DesignWorkflowResult:
        diagnostics = result.final_diagnostics.to_dict() if result.final_diagnostics else None
        analysis = result.final_analysis.to_dict() if result.final_analysis else None

        history: list[dict[str, Any]] = []
        for attempt in result.attempts:
            data = attempt.to_dict()
            history.append({
                "attempt_number": data.get("attempt_number"),
                "status": data.get("status"),
                "passed": data.get("passed", False),
                "compile_success": data.get("compile_success", False),
                "simulation_success": data.get("simulation_success", False),
                "duration_ms": data.get("duration_ms", 0),
                "stdout": data.get("stdout", ""),
                "stderr": data.get("stderr", ""),
                "diagnostics": data.get("diagnostics"),
                "failure_analysis": data.get("failure_analysis"),
                "repair": data.get("repair"),
            })

        testbench_source = result.testbench_source
        if hasattr(testbench_source, "testbench_source"):
            testbench_source = testbench_source.testbench_source

        return DesignWorkflowResult(
            verified=result.verified,
            status=result.status.value,
            specification=result.specification,
            rtl_source=result.rtl_source,
            testbench_source=str(testbench_source or ""),
            attempts=result.total_attempts,
            duration_ms=result.total_duration_ms,
            message=result.final_message,
            diagnostics=diagnostics,
            analysis=analysis,
            verification_history=history,
        )

    def _normalize_specification(self, specification: str) -> str:
        if specification is None:
            raise DesignServiceError("Hardware specification is required.")
        specification = specification.strip()
        if not specification:
            raise DesignServiceError("Hardware specification cannot be empty.")
        if len(specification) > 20_000:
            raise DesignServiceError("Hardware specification is too long. Please keep it below 20,000 characters.")
        return specification


design_service = DesignService()