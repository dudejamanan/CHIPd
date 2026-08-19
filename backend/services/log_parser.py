"""
Silica EDA Platform
===================

Icarus Verilog diagnostic parser.

Converts raw compiler/simulation output into structured diagnostics
that can be consumed by the AI failure-analysis layer.

Example input:

    design.sv:17: syntax error
    design.sv:17: error: malformed statement

Example output:

    Diagnostic(
        severity="error",
        source="design.sv",
        line=17,
        column=None,
        message="syntax error",
    )
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable


# ============================================================================
# Diagnostic
# ============================================================================


@dataclass(slots=True)
class Diagnostic:
    """
    A single normalized compiler/simulation diagnostic.
    """

    severity: str
    source: str | None
    line: int | None
    column: int | None
    message: str
    raw_line: str

    def to_dict(self) -> dict:
        """Convert diagnostic to a JSON-compatible dictionary."""

        return asdict(self)


# ============================================================================
# Diagnostic Report
# ============================================================================


@dataclass(slots=True)
class DiagnosticReport:
    """
    Complete parsed diagnostic report.
    """

    diagnostics: list[Diagnostic]

    error_count: int

    warning_count: int

    info_count: int

    raw_output: str

    summary: str

    def to_dict(self) -> dict:
        """Convert report to a JSON-compatible dictionary."""

        return {
            "diagnostics": [
                diagnostic.to_dict()
                for diagnostic in self.diagnostics
            ],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "raw_output": self.raw_output,
            "summary": self.summary,
        }


# ============================================================================
# Log Parser
# ============================================================================


class VerilogLogParser:
    """
    Parses Icarus Verilog compiler and simulation output.

    The parser is intentionally tolerant because compiler output can vary
    slightly between Icarus versions and operating systems.
    """

    # ------------------------------------------------------------------------
    # Icarus patterns
    # ------------------------------------------------------------------------

    # Examples:
    #
    # design.sv:17: syntax error
    #
    # design.sv:17: error: malformed statement
    #
    # testbench.sv:22: warning: ...
    #
    SOURCE_LINE_PATTERN = re.compile(
        r"""
        ^
        (?P<source>
            .+?
        )
        :
        (?P<line>
            \d+
        )
        (?:
            :
            (?P<column>
                \d+
            )
        )?
        :
        (?:
            \s*
        )
        (?:
            (?P<severity>
                error
                |warning
                |fatal
                |info
            )
                \s*:\s*
        )?
        (?P<message>.+?)
        $
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # Examples:
    #
    # error: something went wrong
    # warning: unused signal
    # ERROR: ...
    SEVERITY_PATTERN = re.compile(
        r"""
        \b
        (?P<severity>
            error
            |warning
            |fatal
            |info
        )
        \s*:\s*
        (?P<message>.+)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # Runtime assertion-like output.
    RUNTIME_FAILURE_PATTERN = re.compile(
        r"""
        \b
        (?P<severity>
            fail
            |failed
            |mismatch
            |fatal
            |error
        )
        \b
        (?:
            \s*:\s*
            (?P<message>.*)
        )?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def parse(
        self,
        output: str,
        *,
        default_source: str | None = None,
    ) -> DiagnosticReport:
        """
        Parse compiler/simulation output.

        Parameters
        ----------
        output:
            Raw Icarus stdout/stderr.

        default_source:
            Optional source filename to use when a diagnostic doesn't
            explicitly contain one.

        Returns
        -------
        DiagnosticReport
        """

        if not output:
            return DiagnosticReport(
                diagnostics=[],
                error_count=0,
                warning_count=0,
                info_count=0,
                raw_output="",
                summary="No diagnostic output.",
            )

        diagnostics: list[Diagnostic] = []

        for raw_line in output.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            diagnostic = self._parse_line(
                line,
                default_source=default_source,
            )

            if diagnostic is not None:
                diagnostics.append(
                    diagnostic
                )

        # --------------------------------------------------------------------
        # Deduplicate
        # --------------------------------------------------------------------

        diagnostics = self._deduplicate(
            diagnostics
        )

        # --------------------------------------------------------------------
        # Counts
        # --------------------------------------------------------------------

        error_count = sum(
            1
            for diagnostic in diagnostics
            if diagnostic.severity in {
                "error",
                "fatal",
            }
        )

        warning_count = sum(
            1
            for diagnostic in diagnostics
            if diagnostic.severity == "warning"
        )

        info_count = sum(
            1
            for diagnostic in diagnostics
            if diagnostic.severity == "info"
        )

        # --------------------------------------------------------------------
        # Summary
        # --------------------------------------------------------------------

        summary = self._build_summary(
            diagnostics=diagnostics,
            error_count=error_count,
            warning_count=warning_count,
        )

        return DiagnosticReport(
            diagnostics=diagnostics,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            raw_output=output,
            summary=summary,
        )

    # ------------------------------------------------------------------------
    # Parse line
    # ------------------------------------------------------------------------

    def _parse_line(
        self,
        line: str,
        *,
        default_source: str | None,
    ) -> Diagnostic | None:
        """
        Parse one output line.
        """

        # ---------------------------------------------------------------
        # First try source:line:column: message
        # or source:line: message
        # ---------------------------------------------------------------

        match = self.SOURCE_LINE_PATTERN.match(
            line
        )

        if match:

            source = (
                match.group("source")
                or default_source
            )

            line_number = self._to_int(
                match.group("line")
            )

            column_number = self._to_int(
                match.group("column")
            )

            severity = (
                match.group("severity")
                or self._infer_severity(
                    match.group("message")
                )
            )

            message = (
                match.group("message")
                .strip()
            )

            return Diagnostic(
                severity=self._normalize_severity(
                    severity
                ),
                source=source,
                line=line_number,
                column=column_number,
                message=message,
                raw_line=line,
            )

        # ---------------------------------------------------------------
        # Generic severity line
        # ---------------------------------------------------------------

        severity_match = self.SEVERITY_PATTERN.search(
            line
        )

        if severity_match:

            severity = (
                severity_match
                .group("severity")
            )

            message = (
                severity_match
                .group("message")
                .strip()
            )

            return Diagnostic(
                severity=self._normalize_severity(
                    severity
                ),
                source=default_source,
                line=None,
                column=None,
                message=message,
                raw_line=line,
            )

        # ---------------------------------------------------------------
        # Runtime failure
        # ---------------------------------------------------------------

        runtime_match = (
            self.RUNTIME_FAILURE_PATTERN.search(
                line
            )
        )

        if runtime_match:

            severity = (
                runtime_match
                .group("severity")
            )

            message = (
                runtime_match.group("message")
                or line
            )

            message = message.strip()

            return Diagnostic(
                severity=self._normalize_severity(
                    severity
                ),
                source=default_source,
                line=None,
                column=None,
                message=message,
                raw_line=line,
            )

        # ---------------------------------------------------------------
        # Icarus known error phrases without "error:"
        # ---------------------------------------------------------------

        if self._looks_like_error(line):

            return Diagnostic(
                severity="error",
                source=default_source,
                line=None,
                column=None,
                message=line,
                raw_line=line,
            )

        # Not a diagnostic.
        return None

    # ------------------------------------------------------------------------
    # Error detection
    # ------------------------------------------------------------------------

    def _looks_like_error(
        self,
        line: str,
    ) -> bool:
        """
        Detect common compiler failures that don't always contain an
        explicit 'error:' prefix.
        """

        patterns = [
            r"\bsyntax\s+error\b",
            r"\bparse\s+error\b",
            r"\bcompilation\s+failed\b",
            r"\bunknown\s+module\b",
            r"\bundefined\b",
            r"\bundeclared\b",
            r"\bmalformed\b",
            r"\bport\s+.*not\s+found\b",
            r"\bcan'?t\s+find\b",
            r"\bcannot\s+find\b",
            r"\binvalid\b",
        ]

        return any(
            re.search(
                pattern,
                line,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ------------------------------------------------------------------------
    # Severity inference
    # ------------------------------------------------------------------------

    def _infer_severity(
        self,
        message: str,
    ) -> str:
        """
        Infer severity when the compiler doesn't explicitly provide it.
        """

        message_lower = message.lower()

        if any(
            keyword in message_lower
            for keyword in [
                "fatal",
                "error",
                "failed",
                "syntax error",
                "malformed",
                "undefined",
                "undeclared",
            ]
        ):
            return "error"

        if "warning" in message_lower:
            return "warning"

        return "info"

    # ------------------------------------------------------------------------
    # Severity normalization
    # ------------------------------------------------------------------------

    def _normalize_severity(
        self,
        severity: str,
    ) -> str:
        """
        Normalize compiler terminology.
        """

        normalized = severity.lower().strip()

        if normalized in {
            "fatal",
            "error",
            "fail",
            "failed",
        }:
            return "error"

        if normalized == "warning":
            return "warning"

        return "info"

    # ------------------------------------------------------------------------
    # Integer conversion
    # ------------------------------------------------------------------------

    def _to_int(
        self,
        value: str | None,
    ) -> int | None:
        """Safely convert a string to an integer."""

        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------------

    def _deduplicate(
        self,
        diagnostics: Iterable[Diagnostic],
    ) -> list[Diagnostic]:
        """
        Remove duplicate diagnostics while preserving order.
        """

        unique: list[Diagnostic] = []

        seen: set[
            tuple[
                str,
                str | None,
                int | None,
                int | None,
                str,
            ]
        ] = set()

        for diagnostic in diagnostics:

            key = (
                diagnostic.severity,
                diagnostic.source,
                diagnostic.line,
                diagnostic.column,
                diagnostic.message,
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(
                diagnostic
            )

        return unique

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    def _build_summary(
        self,
        *,
        diagnostics: list[Diagnostic],
        error_count: int,
        warning_count: int,
    ) -> str:
        """
        Build a compact human-readable summary.
        """

        if not diagnostics:
            return "No compiler or simulation diagnostics detected."

        if error_count == 0 and warning_count == 0:
            return (
                f"{len(diagnostics)} informational "
                "diagnostic(s) detected."
            )

        parts: list[str] = []

        if error_count:
            parts.append(
                f"{error_count} error(s)"
            )

        if warning_count:
            parts.append(
                f"{warning_count} warning(s)"
            )

        return ", ".join(parts) + " detected."


# ============================================================================
# Shared parser instance
# ============================================================================

log_parser = VerilogLogParser()