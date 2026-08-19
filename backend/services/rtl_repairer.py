"""
Silica EDA Platform
===================

AI-assisted RTL repair service.

Responsibilities
----------------
This service takes an existing RTL design and a structured failure
diagnosis and asks Gemini to produce a corrected version of the RTL.

Important architectural rule:

    Gemini proposes the repair.
    Icarus Verilog validates the repair.

This service itself does NOT decide that a repair is correct.

The orchestration layer is responsible for:

    1. Generating a repair candidate.
    2. Compiling it.
    3. Running the testbench.
    4. Accepting the repair only if verification passes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from backend.config import settings
from backend.services.failure_analyzer import FailureAnalysis
from backend.services.llm_service import (
    LLMError,
    llm_service,
)


# ============================================================================
# Exceptions
# ============================================================================


class RTLRepairError(Exception):
    """Base exception for RTL repair failures."""


class RTLRepairParseError(RTLRepairError):
    """Raised when Gemini returns an unusable repair."""


class RTLRepairValidationError(RTLRepairError):
    """Raised when generated repair fails basic validation."""


# ============================================================================
# Result
# ============================================================================


@dataclass(slots=True)
class RTLRepairResult:
    """
    Candidate RTL produced by Gemini.

    verified is deliberately NOT included as a property of the generated
    result. A candidate is only verified after being passed through the
    simulator.
    """

    rtl_source: str

    explanation: str

    changes: list[str]

    confidence: float

    preserved_interface: bool

    repair_scope: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "rtl_source": self.rtl_source,
            "explanation": self.explanation,
            "changes": self.changes,
            "confidence": self.confidence,
            "preserved_interface": self.preserved_interface,
            "repair_scope": self.repair_scope,
        }


# ============================================================================
# Gemini system prompt
# ============================================================================


RTL_REPAIR_SYSTEM_PROMPT = r"""
You are Silica, an expert semiconductor RTL engineer specializing in
debugging and repairing synthesizable SystemVerilog.

Your job is to repair an existing RTL design based on a verification
failure diagnosis.

============================================================
CRITICAL RULE
============================================================

Return a corrected RTL candidate.

Do NOT claim that the design has been verified.

The corrected RTL will be compiled and simulated separately.

============================================================
REPAIR OBJECTIVE
============================================================

Make the smallest safe correction that resolves the diagnosed failure
while preserving the intended hardware behavior.

============================================================
HARDWARE CORRECTNESS
============================================================

You must:

1. Preserve the original hardware specification.

2. Preserve the DUT module name.

3. Preserve the DUT port names.

4. Preserve port directions.

5. Preserve port widths.

6. Preserve the external interface unless the diagnosis explicitly
   identifies the interface itself as incorrect.

7. Preserve clock behavior.

8. Preserve reset polarity unless the diagnosis explicitly identifies
   reset polarity as incorrect.

9. Avoid unrelated refactoring.

10. Avoid changing architecture unnecessarily.

11. Do not introduce simulation-only behavior into synthesizable RTL.

12. Do not add a testbench.

13. Do not add `$display`, `$finish`, `$monitor`, or other testbench
    constructs to the DUT.

14. Do not use delays in synthesizable RTL.

15. Do not instantiate unsupported external modules.

16. Do not invent functionality that was not requested.

============================================================
REPAIR PRIORITY
============================================================

Prefer fixes in this order:

1. Syntax / compilation correctness
2. Module/interface correctness
3. Width/type correctness
4. Reset correctness
5. Clock/sequential logic correctness
6. Combinational logic correctness
7. Functional behavior

Do not change correct code merely for style.

============================================================
REASONING
============================================================

Use the following evidence:

- hardware specification
- current RTL
- testbench
- compiler diagnostics
- simulation diagnostics
- AI failure diagnosis

If the diagnosis is uncertain, make the smallest change supported
by the available evidence.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Use exactly:

{
    "rtl_source": "complete corrected SystemVerilog source",
    "explanation": "Short explanation of the repair.",
    "changes": [
        "Change 1",
        "Change 2"
    ],
    "confidence": 0.95,
    "preserved_interface": true,
    "repair_scope": "minimal"
}

Rules:

- rtl_source must contain the COMPLETE RTL.
- Do not return a patch.
- Do not return only changed lines.
- Do not use Markdown code fences.
- confidence must be between 0 and 1.
- preserved_interface must be true or false.
- repair_scope must be one of:
    - minimal
    - moderate
    - substantial
- Do not add additional top-level JSON fields.
"""


# ============================================================================
# Repairer
# ============================================================================


class RTLRepairer:
    """
    Generates corrected RTL candidates using Gemini.
    """

    def __init__(self) -> None:

        self.max_rtl_length = (
            settings.max_rtl_length
        )

        self.max_context_length = (
            settings.max_repair_context_length
        )

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def repair(
        self,
        *,
        specification: str,
        rtl_source: str,
        testbench_source: str,
        analysis: FailureAnalysis,
        raw_diagnostics: str = "",
    ) -> RTLRepairResult:
        """
        Generate a corrected RTL candidate.

        The returned candidate must still be compiled and simulated before
        being considered valid.
        """

        self._validate_inputs(
            specification=specification,
            rtl_source=rtl_source,
            testbench_source=testbench_source,
            analysis=analysis,
        )

        prompt = self._build_prompt(
            specification=specification,
            rtl_source=rtl_source,
            testbench_source=testbench_source,
            analysis=analysis,
            raw_diagnostics=raw_diagnostics,
        )

        try:

            response = llm_service.generate(
                system_prompt=RTL_REPAIR_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

        except LLMError as exc:

            raise RTLRepairError(
                f"Gemini RTL repair failed: {exc}"
            ) from exc

        return self._parse_response(
            response
        )

    # ------------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------------

    def _validate_inputs(
        self,
        *,
        specification: str,
        rtl_source: str,
        testbench_source: str,
        analysis: FailureAnalysis,
    ) -> None:
        """Validate repair inputs."""

        if not specification.strip():
            raise RTLRepairError(
                "Specification cannot be empty."
            )

        if not rtl_source.strip():
            raise RTLRepairError(
                "RTL source cannot be empty."
            )

        if not testbench_source.strip():
            raise RTLRepairError(
                "Testbench source cannot be empty."
            )

        if len(rtl_source) > settings.max_rtl_length:
            raise RTLRepairError(
                "RTL source exceeds configured size limit."
            )

        if len(testbench_source) > settings.max_testbench_length:
            raise RTLRepairError(
                "Testbench source exceeds configured size limit."
            )

        if analysis is None:
            raise RTLRepairError(
                "Failure analysis is required."
            )

    # ------------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------------

    def _build_prompt(
        self,
        *,
        specification: str,
        rtl_source: str,
        testbench_source: str,
        analysis: FailureAnalysis,
        raw_diagnostics: str,
    ) -> str:
        """
        Build the repair context sent to Gemini.
        """

        analysis_json = json.dumps(
            analysis.to_dict(),
            indent=2,
        )

        prompt = f"""
Repair the following SystemVerilog RTL.

============================================================
HARDWARE SPECIFICATION
============================================================

{specification.strip()}

============================================================
CURRENT RTL
============================================================

{rtl_source.strip()}

============================================================
TESTBENCH
============================================================

{testbench_source.strip()}

============================================================
FAILURE ANALYSIS
============================================================

{analysis_json}

============================================================
RAW DIAGNOSTICS
============================================================

{raw_diagnostics.strip()}

============================================================
REPAIR TASK
============================================================

Generate a corrected version of the RTL.

Requirements:

- Preserve the requested hardware behavior.
- Preserve the module name.
- Preserve the external interface whenever possible.
- Fix the diagnosed problem.
- Do not modify the testbench.
- Do not add simulation-only code.
- Do not add delays.
- Do not add debugging statements.
- Keep the repair as small as reasonably possible.

Return ONLY the required JSON object.
"""

        if len(prompt) <= self.max_context_length:
            return prompt

        # --------------------------------------------------------------------
        # Defensive truncation.
        #
        # Diagnostics and failure analysis are generally more valuable than
        # excessive raw source/log repetition.
        # --------------------------------------------------------------------

        analysis_text = analysis_json[
            :12000
        ]

        diagnostics_text = raw_diagnostics[
            :6000
        ]

        available = (
            self.max_context_length
            - len(specification)
            - len(analysis_text)
            - len(diagnostics_text)
            - 2500
        )

        if available <= 0:

            return f"""
Repair this SystemVerilog design.

SPECIFICATION:
{specification[:5000]}

FAILURE ANALYSIS:
{analysis_text}

DIAGNOSTICS:
{diagnostics_text}

Return only the required JSON object.
"""

        rtl_budget = int(
            available * 0.60
        )

        testbench_budget = int(
            available * 0.40
        )

        return f"""
Repair this SystemVerilog design.

SPECIFICATION:
{specification}

CURRENT RTL:
{rtl_source[:rtl_budget]}

TESTBENCH:
{testbench_source[:testbench_budget]}

FAILURE ANALYSIS:
{analysis_text}

DIAGNOSTICS:
{diagnostics_text}

Return only the required JSON object.
"""

    # ------------------------------------------------------------------------
    # Parse response
    # ------------------------------------------------------------------------

    def _parse_response(
        self,
        response: str,
    ) -> RTLRepairResult:
        """
        Parse Gemini's repair response.
        """

        cleaned = self._extract_json(
            response
        )

        try:

            payload = json.loads(
                cleaned
            )

        except json.JSONDecodeError as exc:

            raise RTLRepairParseError(
                "Gemini returned invalid JSON for RTL repair."
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):

            raise RTLRepairParseError(
                "RTL repair response must be a JSON object."
            )

        self._validate_payload(
            payload
        )

        rtl_source = self._clean_rtl(
            str(
                payload["rtl_source"]
            )
        )

        self._validate_rtl(
            rtl_source
        )

        return RTLRepairResult(
            rtl_source=rtl_source,
            explanation=str(
                payload["explanation"]
            ),
            changes=[
                str(item)
                for item in payload["changes"]
            ],
            confidence=float(
                payload["confidence"]
            ),
            preserved_interface=bool(
                payload["preserved_interface"]
            ),
            repair_scope=str(
                payload["repair_scope"]
            ),
        )

    # ------------------------------------------------------------------------
    # Extract JSON
    # ------------------------------------------------------------------------

    def _extract_json(
        self,
        response: str,
    ) -> str:
        """
        Extract JSON from Gemini response.

        Gemini occasionally adds Markdown fences despite instructions,
        so we defensively remove them.
        """

        text = response.strip()

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

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:

            raise RTLRepairParseError(
                "No JSON object found in Gemini repair response."
            )

        return text[
            start:end + 1
        ]

    # ------------------------------------------------------------------------
    # Validate JSON schema
    # ------------------------------------------------------------------------

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        """Validate Gemini repair response."""

        required = {
            "rtl_source",
            "explanation",
            "changes",
            "confidence",
            "preserved_interface",
            "repair_scope",
        }

        missing = (
            required
            - payload.keys()
        )

        if missing:

            raise RTLRepairParseError(
                "Gemini repair response is missing fields: "
                + ", ".join(
                    sorted(missing)
                )
            )

        # --------------------------------------------------------------------
        # RTL
        # --------------------------------------------------------------------

        if not isinstance(
            payload["rtl_source"],
            str,
        ):

            raise RTLRepairParseError(
                "rtl_source must be a string."
            )

        if not payload[
            "rtl_source"
        ].strip():

            raise RTLRepairParseError(
                "rtl_source cannot be empty."
            )

        # --------------------------------------------------------------------
        # Changes
        # --------------------------------------------------------------------

        if not isinstance(
            payload["changes"],
            list,
        ):

            raise RTLRepairParseError(
                "changes must be an array."
            )

        if len(
            payload["changes"]
        ) > 20:

            raise RTLRepairParseError(
                "Too many changes returned."
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

            raise RTLRepairParseError(
                "confidence must be numeric."
            ) from exc

        if not 0.0 <= confidence <= 1.0:

            raise RTLRepairParseError(
                "confidence must be between 0 and 1."
            )

        # --------------------------------------------------------------------
        # Interface flag
        # --------------------------------------------------------------------

        if not isinstance(
            payload["preserved_interface"],
            bool,
        ):

            raise RTLRepairParseError(
                "preserved_interface must be boolean."
            )

        # --------------------------------------------------------------------
        # Scope
        # --------------------------------------------------------------------

        scope = str(
            payload["repair_scope"]
        )

        if scope not in {
            "minimal",
            "moderate",
            "substantial",
        }:

            raise RTLRepairParseError(
                f"Invalid repair scope: {scope}"
            )

    # ------------------------------------------------------------------------
    # Clean RTL
    # ------------------------------------------------------------------------

    def _clean_rtl(
        self,
        rtl_source: str,
    ) -> str:
        """
        Remove Markdown fences and accidental prose.
        """

        text = rtl_source.strip()

        text = re.sub(
            r"^\s*```(?:systemverilog|verilog|sv)?\s*",
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

        # ---------------------------------------------------------------
        # Find module declaration.
        # ---------------------------------------------------------------

        module_match = re.search(
            r"\bmodule\s+[A-Za-z_][A-Za-z0-9_]*\b",
            text,
        )

        if module_match is None:

            raise RTLRepairValidationError(
                "Repaired RTL contains no module declaration."
            )

        # Remove accidental prose before module.
        text = text[
            module_match.start():
        ]

        # ---------------------------------------------------------------
        # Keep through final endmodule.
        # ---------------------------------------------------------------

        endmodule_matches = list(
            re.finditer(
                r"\bendmodule\b",
                text,
            )
        )

        if not endmodule_matches:

            raise RTLRepairValidationError(
                "Repaired RTL contains no endmodule."
            )

        text = text[
            :endmodule_matches[-1].end()
        ]

        return text.strip()

    # ------------------------------------------------------------------------
    # Basic RTL validation
    # ------------------------------------------------------------------------

    def _validate_rtl(
        self,
        rtl_source: str,
    ) -> None:
        """
        Lightweight structural validation.

        Full correctness is determined later by Icarus.
        """

        if not rtl_source.strip():

            raise RTLRepairValidationError(
                "Repaired RTL is empty."
            )

        if len(rtl_source) > self.max_rtl_length:

            raise RTLRepairValidationError(
                "Repaired RTL exceeds the configured size limit."
            )

        # ---------------------------------------------------------------
        # Module
        # ---------------------------------------------------------------

        modules = re.findall(
            r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b",
            rtl_source,
        )

        if not modules:

            raise RTLRepairValidationError(
                "No valid module declaration found."
            )

        # Multiple modules are technically valid SystemVerilog, but for
        # the MVP we keep generated DUTs intentionally simple.
        if len(modules) > 3:

            raise RTLRepairValidationError(
                "Repaired RTL contains an excessive number of modules."
            )

        # ---------------------------------------------------------------
        # endmodule
        # ---------------------------------------------------------------

        if not re.search(
            r"\bendmodule\b",
            rtl_source,
        ):

            raise RTLRepairValidationError(
                "Missing endmodule."
            )

        # ---------------------------------------------------------------
        # Basic delimiter balance
        # ---------------------------------------------------------------

        if rtl_source.count("(") != rtl_source.count(")"):

            raise RTLRepairValidationError(
                "Unbalanced parentheses in repaired RTL."
            )

        if rtl_source.count("[") != rtl_source.count("]"):

            raise RTLRepairValidationError(
                "Unbalanced square brackets in repaired RTL."
            )

        # ---------------------------------------------------------------
        # Never allow obvious testbench constructs.
        # ---------------------------------------------------------------

        forbidden_patterns = [
            r"\$finish\b",
            r"\$fatal\b",
            r"\$display\b",
            r"\$monitor\b",
            r"\$dumpfile\b",
            r"\$dumpvars\b",
        ]

        for pattern in forbidden_patterns:

            if re.search(
                pattern,
                rtl_source,
                flags=re.IGNORECASE,
            ):

                raise RTLRepairValidationError(
                    "Repaired RTL contains testbench-only construct: "
                    f"{pattern}"
                )

        # ---------------------------------------------------------------
        # Reject Markdown.
        # ---------------------------------------------------------------

        if "```" in rtl_source:

            raise RTLRepairValidationError(
                "Repaired RTL contains Markdown code fences."
            )


# ============================================================================
# Shared instance
# ============================================================================

rtl_repairer = RTLRepairer()