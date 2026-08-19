"""
Silica EDA Platform
===================

AI-assisted RTL failure analysis.

This service takes:
    - original hardware specification
    - generated RTL
    - generated testbench
    - simulation status
    - structured compiler/simulation diagnostics

and asks Gemini to determine:

    1. What failed?
    2. Why did it fail?
    3. Which part of the design is responsible?
    4. What should be changed?
    5. How confident is the diagnosis?

The analyzer does NOT modify RTL.

A separate repair service is responsible for generating a corrected
implementation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from backend.config import settings
from backend.services.llm_service import (
    LLMError,
    llm_service,
)
from backend.services.log_parser import (
    DiagnosticReport,
)


# ============================================================================
# Exceptions
# ============================================================================


class FailureAnalysisError(Exception):
    """Base exception for failure-analysis errors."""


class FailureAnalysisParseError(FailureAnalysisError):
    """Raised when Gemini returns invalid analysis output."""


# ============================================================================
# Analysis result
# ============================================================================


@dataclass(slots=True)
class FailureAnalysis:
    """
    Structured AI diagnosis of a verification failure.
    """

    failed: bool

    error_category: str

    root_cause: str

    explanation: str

    affected_file: str | None

    affected_line: int | None

    suggested_fix: str

    confidence: float

    evidence: list[str] = field(
        default_factory=list
    )

    repair_priority: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "failed": self.failed,
            "error_category": self.error_category,
            "root_cause": self.root_cause,
            "explanation": self.explanation,
            "affected_file": self.affected_file,
            "affected_line": self.affected_line,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "repair_priority": self.repair_priority,
        }


# ============================================================================
# Gemini system prompt
# ============================================================================


FAILURE_ANALYSIS_SYSTEM_PROMPT = r"""
You are Silica, an expert semiconductor RTL verification engineer.

You analyze failures produced while compiling and simulating
SystemVerilog designs.

Your job is NOT to rewrite the RTL.

Your job is to diagnose the failure accurately.

============================================================
INPUTS
============================================================

You will receive:

1. Hardware specification
2. Generated RTL
3. Generated testbench
4. Verification status
5. Structured diagnostics
6. Raw compiler/simulation output when available

============================================================
ANALYSIS OBJECTIVES
============================================================

Determine:

1. Whether the design actually failed.

2. The most likely error category.

3. The root cause.

4. The exact location responsible, if identifiable.

5. Why the failure occurred.

6. The minimal conceptual correction required.

7. How confident you are in the diagnosis.

============================================================
ERROR CATEGORIES
============================================================

Choose exactly one:

- syntax_error
- elaboration_error
- interface_mismatch
- width_mismatch
- undeclared_signal
- unknown_module
- reset_logic_error
- clocking_error
- sequential_logic_error
- combinational_logic_error
- functional_error
- assertion_failure
- testbench_error
- simulator_error
- timeout
- unknown

============================================================
IMPORTANT REASONING RULES
============================================================

1. Do not assume the RTL is wrong merely because simulation failed.

2. The testbench itself may be wrong.

3. Distinguish:
       RTL bug
       testbench bug
       compilation issue
       simulator/runtime issue

4. Prefer evidence from compiler messages and simulation output.

5. If a line number is provided, inspect that section of RTL carefully.

6. Check module names and port names.

7. Check signal widths.

8. Check signed versus unsigned behavior where relevant.

9. Check reset polarity and reset timing.

10. Check clock edge sensitivity.

11. Check blocking versus non-blocking assignments.

12. Check combinational completeness.

13. Check whether expected behavior in the testbench matches the
    hardware specification.

14. Do not invent errors that are not supported by the evidence.

15. If the evidence is insufficient, say so and lower confidence.

============================================================
CONFIDENCE
============================================================

Return a confidence value between 0 and 1.

Use approximately:

0.90 - 1.00
Very strong evidence.

0.75 - 0.89
Strong evidence.

0.50 - 0.74
Plausible diagnosis but some uncertainty.

0.25 - 0.49
Weak evidence.

0.00 - 0.24
Very uncertain.

============================================================
REPAIR PRIORITY
============================================================

Choose:

- critical
- high
- medium
- low

Use critical/high for errors preventing compilation or verification.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Use exactly this structure:

{
    "failed": true,
    "error_category": "syntax_error",
    "root_cause": "Short description of the root cause.",
    "explanation": "Detailed but concise explanation.",
    "affected_file": "design.sv",
    "affected_line": 17,
    "suggested_fix": "Describe the minimal correction.",
    "confidence": 0.95,
    "evidence": [
        "Evidence item 1",
        "Evidence item 2"
    ],
    "repair_priority": "high"
}

Rules:

- confidence must be a number between 0 and 1.
- affected_line must be an integer or null.
- affected_file must be a string or null.
- evidence must be an array of strings.
- Do not wrap JSON in Markdown.
- Do not include additional top-level fields.
"""


# ============================================================================
# Analyzer
# ============================================================================


class FailureAnalyzer:
    """
    Uses Gemini to diagnose RTL verification failures.
    """

    def __init__(self) -> None:

        self.max_context_length = (
            settings.max_analysis_context_length
        )

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def analyze(
        self,
        *,
        specification: str,
        rtl_source: str,
        testbench_source: str,
        status: str,
        diagnostics: DiagnosticReport | None = None,
        raw_output: str = "",
    ) -> FailureAnalysis:
        """
        Analyze a verification result.

        Parameters
        ----------
        specification:
            Original natural-language hardware requirement.

        rtl_source:
            Generated SystemVerilog RTL.

        testbench_source:
            Generated SystemVerilog testbench.

        status:
            Verification status from simulator.

        diagnostics:
            Parsed Icarus diagnostics.

        raw_output:
            Raw stdout/stderr when useful.

        Returns
        -------
        FailureAnalysis
        """

        if not specification.strip():
            raise FailureAnalysisError(
                "Specification cannot be empty."
            )

        if not rtl_source.strip():
            raise FailureAnalysisError(
                "RTL source cannot be empty."
            )

        if not testbench_source.strip():
            raise FailureAnalysisError(
                "Testbench source cannot be empty."
            )

        context = self._build_context(
            specification=specification,
            rtl_source=rtl_source,
            testbench_source=testbench_source,
            status=status,
            diagnostics=diagnostics,
            raw_output=raw_output,
        )

        try:

            response = llm_service.generate(
                system_prompt=FAILURE_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=context,
            )

        except LLMError as exc:

            raise FailureAnalysisError(
                f"Gemini failure analysis failed: {exc}"
            ) from exc

        return self._parse_response(
            response
        )

    # ------------------------------------------------------------------------
    # Build context
    # ------------------------------------------------------------------------

    def _build_context(
        self,
        *,
        specification: str,
        rtl_source: str,
        testbench_source: str,
        status: str,
        diagnostics: DiagnosticReport | None,
        raw_output: str,
    ) -> str:
        """
        Construct a compact but information-rich Gemini prompt.
        """

        diagnostic_json = "{}"

        if diagnostics is not None:

            diagnostic_json = json.dumps(
                diagnostics.to_dict(),
                indent=2,
            )

        context = f"""
Analyze the following SystemVerilog verification result.

============================================================
HARDWARE SPECIFICATION
============================================================

{specification.strip()}

============================================================
VERIFICATION STATUS
============================================================

{status}

============================================================
GENERATED RTL
============================================================

{rtl_source.strip()}

============================================================
GENERATED TESTBENCH
============================================================

{testbench_source.strip()}

============================================================
STRUCTURED DIAGNOSTICS
============================================================

{diagnostic_json}

============================================================
RAW SIMULATION / COMPILER OUTPUT
============================================================

{raw_output.strip()}

============================================================
TASK
============================================================

Determine the most likely root cause.

Pay special attention to whether the failure originates from:

- RTL
- testbench
- module/interface mismatch
- compilation
- simulation runtime
- functional behavior

Return only the required JSON object.
"""

        # --------------------------------------------------------------------
        # Guard against unexpectedly huge context.
        # --------------------------------------------------------------------

        if len(context) <= self.max_context_length:
            return context

        # Preserve the most useful information first.
        #
        # We prefer:
        #   specification
        #   diagnostics
        #   RTL
        #   testbench
        #   raw logs
        #
        # In normal MVP usage this limit should not be reached.
        # This fallback protects the API from accidental oversized input.

        remaining = (
            self.max_context_length
            - len(specification)
            - len(diagnostic_json)
            - 2000
        )

        if remaining <= 0:

            return (
                "Analyze this verification failure.\n\n"
                f"SPECIFICATION:\n{specification[:4000]}\n\n"
                f"STATUS:\n{status}\n\n"
                f"DIAGNOSTICS:\n{diagnostic_json[:8000]}"
            )

        rtl_budget = int(
            remaining * 0.55
        )

        testbench_budget = int(
            remaining * 0.30
        )

        raw_budget = int(
            remaining * 0.15
        )

        return f"""
Analyze this SystemVerilog verification failure.

============================================================
SPECIFICATION
============================================================

{specification}

============================================================
STATUS
============================================================

{status}

============================================================
RTL
============================================================

{rtl_source[:rtl_budget]}

============================================================
TESTBENCH
============================================================

{testbench_source[:testbench_budget]}

============================================================
STRUCTURED DIAGNOSTICS
============================================================

{diagnostic_json}

============================================================
RAW OUTPUT
============================================================

{raw_output[:raw_budget]}

Return only the required JSON object.
"""

    # ------------------------------------------------------------------------
    # Parse Gemini response
    # ------------------------------------------------------------------------

    def _parse_response(
        self,
        response: str,
    ) -> FailureAnalysis:
        """
        Parse and validate Gemini's JSON response.
        """

        cleaned = self._clean_json(
            response
        )

        try:

            payload = json.loads(
                cleaned
            )

        except json.JSONDecodeError as exc:

            raise FailureAnalysisParseError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise FailureAnalysisParseError(
                "Gemini analysis response must be a JSON object."
            )

        self._validate_payload(
            payload
        )

        return FailureAnalysis(
            failed=bool(
                payload["failed"]
            ),
            error_category=str(
                payload["error_category"]
            ),
            root_cause=str(
                payload["root_cause"]
            ),
            explanation=str(
                payload["explanation"]
            ),
            affected_file=(
                str(payload["affected_file"])
                if payload["affected_file"] is not None
                else None
            ),
            affected_line=(
                int(payload["affected_line"])
                if payload["affected_line"] is not None
                else None
            ),
            suggested_fix=str(
                payload["suggested_fix"]
            ),
            confidence=float(
                payload["confidence"]
            ),
            evidence=[
                str(item)
                for item in payload["evidence"]
            ],
            repair_priority=str(
                payload["repair_priority"]
            ),
        )

    # ------------------------------------------------------------------------
    # Clean JSON
    # ------------------------------------------------------------------------

    def _clean_json(
        self,
        response: str,
    ) -> str:
        """
        Remove accidental Markdown fences or surrounding prose.
        """

        text = response.strip()

        # Remove Markdown JSON fences.
        text = re.sub(
            r"^\s*```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```\s*$",
            "",
            text,
        )

        text = text.strip()

        # --------------------------------------------------------------------
        # If Gemini added prose around the JSON, extract the outer object.
        # --------------------------------------------------------------------

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:

            raise FailureAnalysisParseError(
                "No JSON object found in Gemini response."
            )

        return text[
            start:end + 1
        ]

    # ------------------------------------------------------------------------
    # Validate payload
    # ------------------------------------------------------------------------

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Validate the response schema before constructing the result.
        """

        required_fields = {
            "failed",
            "error_category",
            "root_cause",
            "explanation",
            "affected_file",
            "affected_line",
            "suggested_fix",
            "confidence",
            "evidence",
            "repair_priority",
        }

        missing = (
            required_fields
            - payload.keys()
        )

        if missing:

            raise FailureAnalysisParseError(
                "Gemini response is missing fields: "
                + ", ".join(
                    sorted(missing)
                )
            )

        valid_categories = {
            "syntax_error",
            "elaboration_error",
            "interface_mismatch",
            "width_mismatch",
            "undeclared_signal",
            "unknown_module",
            "reset_logic_error",
            "clocking_error",
            "sequential_logic_error",
            "combinational_logic_error",
            "functional_error",
            "assertion_failure",
            "testbench_error",
            "simulator_error",
            "timeout",
            "unknown",
        }

        category = str(
            payload["error_category"]
        )

        if category not in valid_categories:

            raise FailureAnalysisParseError(
                f"Invalid error category: {category}"
            )

        # --------------------------------------------------------------------
        # Confidence
        # --------------------------------------------------------------------

        try:
            confidence = float(
                payload["confidence"]
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise FailureAnalysisParseError(
                "Confidence must be numeric."
            ) from exc

        if not 0.0 <= confidence <= 1.0:

            raise FailureAnalysisParseError(
                "Confidence must be between 0 and 1."
            )

        # --------------------------------------------------------------------
        # Affected line
        # --------------------------------------------------------------------

        affected_line = payload[
            "affected_line"
        ]

        if affected_line is not None:

            try:
                line_number = int(
                    affected_line
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise FailureAnalysisParseError(
                    "affected_line must be an integer or null."
                ) from exc

            if line_number < 1:

                raise FailureAnalysisParseError(
                    "affected_line must be >= 1."
                )

        # --------------------------------------------------------------------
        # Evidence
        # --------------------------------------------------------------------

        evidence = payload[
            "evidence"
        ]

        if not isinstance(
            evidence,
            list,
        ):

            raise FailureAnalysisParseError(
                "evidence must be an array."
            )

        if len(evidence) > 20:

            raise FailureAnalysisParseError(
                "Too many evidence items returned."
            )

        # --------------------------------------------------------------------
        # Repair priority
        # --------------------------------------------------------------------

        priority = str(
            payload["repair_priority"]
        )

        if priority not in {
            "critical",
            "high",
            "medium",
            "low",
        }:

            raise FailureAnalysisParseError(
                f"Invalid repair priority: {priority}"
            )


# ============================================================================
# Shared analyzer instance
# ============================================================================

failure_analyzer = FailureAnalyzer()