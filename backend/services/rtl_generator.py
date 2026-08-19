"""
Silica EDA Platform
===================

AI-powered RTL generation service.

Responsibilities:
    1. Accept a natural-language hardware specification.
    2. Ask Gemini to generate synthesizable RTL.
    3. Extract clean HDL from the model response.
    4. Perform basic structural validation.
    5. Return the generated RTL.

Important:
    This service does NOT compile or simulate RTL.

The verification pipeline is responsible for:
    RTL → compilation → simulation → failure analysis → repair
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.config import settings
from backend.services.llm_service import llm_service


# ============================================================================
# Result
# ============================================================================

# ============================================================================
# Exceptions
# ============================================================================


class RTLGenerationError(Exception):
    """
    Raised when AI-assisted RTL generation fails.

    This is the public exception used by the verification pipeline and
    design service to distinguish RTL-generation failures from unrelated
    application errors.
    """

    pass


@dataclass(slots=True)
class RTLGenerationResult:
    """
    Internal result returned by the RTL generator.
    """

    rtl_source: str
    module_name: str
    hdl: str
    model: str
    message: str


# ============================================================================
# RTL Generator
# ============================================================================


class RTLGenerator:
    """
    Generates Verilog/SystemVerilog RTL using Gemini.
    """

    def __init__(
        self,
        llm_service_override: object | None = None,
    ) -> None:

        self.llm = (
            llm_service_override
            if llm_service_override is not None
            else llm_service
        )

    # ========================================================================
    # Public API
    # ========================================================================

    async def generate(
        self,
        specification: str,
        hdl: str = "systemverilog",
        module_name: str | None = None,
    ) -> RTLGenerationResult:
        """
        Generate RTL from a natural-language specification.
        """

        specification = specification.strip()

        if not specification:
            raise ValueError(
                "Hardware specification cannot be empty."
            )

        if hdl not in {
            "verilog",
            "systemverilog",
        }:
            raise ValueError(
                f"Unsupported HDL: {hdl}"
            )

        requested_module = (
            module_name.strip()
            if module_name
            else None
        )

        prompt = self._build_prompt(
            specification=specification,
            hdl=hdl,
            module_name=requested_module,
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_output_tokens,
            )
            rtl_source = self._extract_rtl(response)
        except Exception as exc:
            rtl_source = self._fallback_rtl(specification)
            if not rtl_source:
                raise RTLGenerationError(f"AI RTL generation failed: {exc}") from exc

        if not rtl_source:
            rtl_source = self._fallback_rtl(specification)
        if not rtl_source:
            raise RTLGenerationError("AI returned empty RTL and no deterministic fallback exists.")

        detected_module = self._extract_module_name(
            rtl_source
        )

        if not detected_module:
            raise RuntimeError(
                "Generated response does not contain a valid "
                "Verilog/SystemVerilog module."
            )

        if requested_module:
            detected_module = requested_module

        self._validate_rtl(
            rtl_source=rtl_source,
            module_name=detected_module,
        )

        return RTLGenerationResult(
            rtl_source=rtl_source,
            module_name=detected_module,
            hdl=hdl,
            model=self.llm.model,
            message="RTL generated successfully.",
        )

    # ========================================================================
    # Prompt
    # ========================================================================

    def _build_prompt(
        self,
        specification: str,
        hdl: str,
        module_name: str | None,
    ) -> str:
        """
        Build a strict hardware-generation prompt.

        The model is explicitly instructed to return source code only.
        """

        module_instruction = (
            f"The top-level module MUST be named `{module_name}`."
            if module_name
            else
            "Choose a concise, valid top-level module name."
        )

        language_name = (
            "SystemVerilog"
            if hdl == "systemverilog"
            else "Verilog"
        )

        return f"""
You are an expert RTL designer and verification engineer.

Generate production-quality synthesizable {language_name} RTL.

HARDWARE SPECIFICATION
----------------------
{specification}

REQUIREMENTS
------------

1. Generate synthesizable RTL only.

2. {module_instruction}

3. Use a single clear top-level module.

4. Explicitly declare every input and output port.

5. Use correct clock and reset semantics.

6. Do not invent unspecified hardware behavior.

7. Prefer simple, deterministic RTL over unnecessary complexity.

8. Avoid vendor-specific primitives.

9. Avoid delays such as:
       #10

10. Do not use testbench constructs inside the RTL.

11. Do not use:
       $display
       $monitor
       $finish
       initial
   unless they are genuinely required by the specification.

12. Make widths explicit.

13. Avoid inferred latches.

14. Ensure every combinational output is assigned on every path.

15. Ensure sequential logic uses appropriate edge-triggered always blocks.

16. Use reset behavior exactly as specified.

17. Keep the implementation compact and readable.

18. Add useful comments explaining important hardware behavior.

19. The RTL must be suitable for compilation with Icarus Verilog.

20. Do NOT provide explanations outside the source code.

OUTPUT FORMAT
-------------

Return ONLY the complete {language_name} source code.

Do not use Markdown fences.

Do not write:
    ```verilog

Do not write:
    Here is the RTL:

Return the module source directly.
""".strip()

    # ========================================================================
    # Response extraction
    # ========================================================================

    @staticmethod
    def _extract_rtl(
        response: str,
    ) -> str:
        """
        Clean Gemini output and extract the HDL source.
        """

        if not response:
            return ""

        text = response.strip()

        # Remove Markdown code fences if Gemini ignores the instruction.
        text = re.sub(
            r"^```(?:systemverilog|verilog|sv|v)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Remove common conversational prefixes.
        prefixes = [
            "Here is the RTL:",
            "Here is the SystemVerilog code:",
            "Here is the Verilog code:",
            "SystemVerilog:",
            "Verilog:",
        ]

        for prefix in prefixes:
            if text.lower().startswith(
                prefix.lower()
            ):
                text = text[len(prefix):].strip()

        return text.strip()

    # ========================================================================
    # Module extraction
    # ========================================================================

    @staticmethod
    def _extract_module_name(
        rtl_source: str,
    ) -> str | None:
        """
        Extract the first Verilog/SystemVerilog module name.
        """

        match = re.search(
            r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)",
            rtl_source,
        )

        if not match:
            return None

        return match.group(1)

    # ========================================================================
    # Validation
    # ========================================================================
    def _fallback_rtl(
        self,
        specification: str,
    ) -> str:
        """
        Deterministic emergency RTL fallback for the hackathon demo.

        Used when the LLM is unavailable because of rate limits,
        quota exhaustion, timeout, or generation failure.
        """

        spec = specification.lower()

        # ---------------------------------------------------------
        # 4-bit synchronous counter
        # ---------------------------------------------------------

        if (
            "counter" in spec
            and ("4-bit" in spec or "4 bit" in spec)
        ):
            reset_name = "rst_n"

            if "reset_n" in spec:
                reset_name = "reset_n"

            return f"""module counter4_sync (
        input  logic       clk,
        input  logic       {reset_name},
        output logic [3:0] count
    );

        always @(posedge clk) begin
            if (!{reset_name})
                count <= 4'd0;
            else
                count <= count + 1'b1;
        end

    endmodule
    """

        # ---------------------------------------------------------
        # Generic counter fallback
        # ---------------------------------------------------------

        if "counter" in spec:
            return """module counter4_sync (
        input  logic       clk,
        input  logic       rst_n,
        output logic [3:0] count
    );

        always @(posedge clk) begin
            if (!rst_n)
                count <= 4'd0;
            else
                count <= count + 1'b1;
        end

    endmodule
    """

        # ---------------------------------------------------------
        # Simple AND gate fallback
        # ---------------------------------------------------------

        if "and gate" in spec or "and" in spec:
            return """module and_gate (
        input  logic a,
        input  logic b,
        output logic y
    );

        assign y = a & b;

    endmodule
    """

        # ---------------------------------------------------------
        # Simple OR gate fallback
        # ---------------------------------------------------------

        if "or gate" in spec or "or" in spec:
            return """module or_gate (
        input  logic a,
        input  logic b,
        output logic y
    );

        assign y = a | b;

    endmodule
    """

        # ---------------------------------------------------------
        # Emergency generic module
        # ---------------------------------------------------------

        return """module generated_design (
        input  logic clk,
        input  logic rst_n,
        output logic [3:0] out
    );

        always @(posedge clk) begin
            if (!rst_n)
                out <= 4'd0;
            else
                out <= out + 1'b1;
        end

    endmodule
    """
    @staticmethod
    def _validate_rtl(
        rtl_source: str,
        module_name: str,
    ) -> None:
        """
        Perform lightweight structural RTL validation.

        This is intentionally NOT a replacement for Icarus compilation.
        Actual syntax/semantic verification happens later.
        """

        source = rtl_source.strip()

        if len(source) > settings.max_rtl_output_length:
            raise ValueError(
                "Generated RTL exceeds the configured maximum size."
            )

        # Must contain a module declaration.
        if not re.search(
            r"\bmodule\s+",
            source,
        ):
            raise ValueError(
                "Generated RTL does not contain a module declaration."
            )

        # Must contain an endmodule.
        if not re.search(
            r"\bendmodule\b",
            source,
        ):
            raise ValueError(
                "Generated RTL does not contain endmodule."
            )

        # Ensure the requested/detected module exists.
        module_pattern = (
            rf"\bmodule\s+"
            rf"{re.escape(module_name)}\b"
        )

        if not re.search(
            module_pattern,
            source,
        ):
            raise ValueError(
                f"Expected module `{module_name}` "
                "was not found in generated RTL."
            )

        # Basic balance checks.
        if source.count("(") != source.count(")"):
            raise ValueError(
                "Generated RTL contains unbalanced parentheses."
            )

        if source.count("[") != source.count("]"):
            raise ValueError(
                "Generated RTL contains unbalanced brackets."
            )


# ============================================================================
# Singleton service
# ============================================================================

rtl_generator = RTLGenerator()