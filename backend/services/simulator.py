"""
Silica EDA Platform
===================

Local SystemVerilog simulation service.

Uses Icarus Verilog:

    RTL + Testbench
          ↓
       iverilog
          ↓
    Compiled simulation
          ↓
         vvp
          ↓
     PASS / FAIL

No Docker is required.

The simulator is deliberately isolated from the API layer so that:
    - subprocess handling stays in one place
    - timeouts are controlled
    - stdout/stderr are captured
    - generated files are kept isolated
    - simulation results have a stable structure
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from backend.config import settings


# ============================================================================
# Exceptions
# ============================================================================


class SimulationError(Exception):
    """Base exception for simulation failures."""


class SimulatorNotFoundError(SimulationError):
    """Raised when Icarus Verilog is not installed or cannot be found."""


class CompilationError(SimulationError):
    """Raised when RTL/testbench compilation fails."""


class SimulationTimeoutError(SimulationError):
    """Raised when simulation exceeds the configured timeout."""


# ============================================================================
# Result
# ============================================================================


@dataclass(slots=True)
class SimulationResult:
    """
    Normalized result of compilation + simulation.

    The API layer can safely serialize this object without knowing anything
    about subprocesses or filesystem details.
    """

    success: bool

    status: str

    compile_stdout: str

    compile_stderr: str

    simulation_stdout: str

    simulation_stderr: str

    exit_code: int | None

    duration_seconds: float

    rtl_path: str | None = None

    testbench_path: str | None = None

    executable_path: str | None = None

    error_summary: str | None = None


# ============================================================================
# Simulator
# ============================================================================


class IcarusSimulator:
    """
    Local Icarus Verilog simulator.

    The simulator creates an isolated temporary directory for every run.

    Example:

        result = simulator.run(
            rtl_source=rtl,
            testbench_source=testbench,
            module_name="counter_4bit",
        )
    """

    def __init__(
        self,
        *,
        simulator_binary: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:

        self.simulator_binary = (
            simulator_binary
            or settings.simulator
        )

        self.timeout_seconds = (
            timeout_seconds
            or settings.simulation_timeout_seconds
        )

        self._resolved_binary: str | None = None

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------

    def run(
        self,
        *,
        rtl_source: str,
        testbench_source: str,
        module_name: str,
    ) -> SimulationResult:
        """
        Compile and simulate the supplied RTL/testbench.

        Parameters
        ----------
        rtl_source:
            Generated SystemVerilog RTL.

        testbench_source:
            Generated SystemVerilog testbench.

        module_name:
            DUT module name.

        Returns
        -------
        SimulationResult
            Structured compile/simulation result.
        """

        self._validate_inputs(
            rtl_source=rtl_source,
            testbench_source=testbench_source,
            module_name=module_name,
        )

        binary = self._find_simulator()

        start_time = time.perf_counter()

        # --------------------------------------------------------------------
        # Temporary workspace
        # --------------------------------------------------------------------

        with tempfile.TemporaryDirectory(
            prefix="silica_sim_",
        ) as temp_dir:

            workspace = Path(temp_dir)

            rtl_path = workspace / "design.sv"
            testbench_path = workspace / "testbench.sv"
            executable_path = workspace / "simulation.out"

            rtl_path.write_text(
                rtl_source,
                encoding="utf-8",
            )

            testbench_path.write_text(
                testbench_source,
                encoding="utf-8",
            )

            # ---------------------------------------------------------------
            # Compilation
            # ---------------------------------------------------------------

            compile_result = self._compile(
                binary=binary,
                rtl_path=rtl_path,
                testbench_path=testbench_path,
                executable_path=executable_path,
            )

            if compile_result.returncode != 0:

                duration = (
                    time.perf_counter()
                    - start_time
                )

                return SimulationResult(
                    success=False,
                    status="compile_error",
                    compile_stdout=(
                        compile_result.stdout
                        or ""
                    ),
                    compile_stderr=(
                        compile_result.stderr
                        or ""
                    ),
                    simulation_stdout="",
                    simulation_stderr="",
                    exit_code=compile_result.returncode,
                    duration_seconds=duration,
                    rtl_path=str(rtl_path),
                    testbench_path=str(testbench_path),
                    executable_path=str(executable_path),
                    error_summary=self._summarize_compile_error(
                        compile_result.stderr
                    ),
                )

            # ---------------------------------------------------------------
            # Simulation
            # ---------------------------------------------------------------

            try:

                simulation_result = self._simulate(
                    executable_path=executable_path,
                )

            except subprocess.TimeoutExpired:

                duration = (
                    time.perf_counter()
                    - start_time
                )

                return SimulationResult(
                    success=False,
                    status="timeout",
                    compile_stdout=(
                        compile_result.stdout
                        or ""
                    ),
                    compile_stderr=(
                        compile_result.stderr
                        or ""
                    ),
                    simulation_stdout="",
                    simulation_stderr="Simulation exceeded "
                    f"{self.timeout_seconds} seconds.",
                    exit_code=None,
                    duration_seconds=duration,
                    rtl_path=str(rtl_path),
                    testbench_path=str(testbench_path),
                    executable_path=str(executable_path),
                    error_summary=(
                        "Simulation timed out. "
                        "The generated testbench may contain an "
                        "infinite loop or the design may never terminate."
                    ),
                )

            duration = (
                time.perf_counter()
                - start_time
            )

            # ---------------------------------------------------------------
            # Determine verification status
            # ---------------------------------------------------------------

            status = self._determine_status(
                return_code=simulation_result.returncode,
                stdout=simulation_result.stdout or "",
                stderr=simulation_result.stderr or "",
            )

            success = status == "passed"

            return SimulationResult(
                success=success,
                status=status,
                compile_stdout=(
                    compile_result.stdout
                    or ""
                ),
                compile_stderr=(
                    compile_result.stderr
                    or ""
                ),
                simulation_stdout=(
                    simulation_result.stdout
                    or ""
                ),
                simulation_stderr=(
                    simulation_result.stderr
                    or ""
                ),
                exit_code=simulation_result.returncode,
                duration_seconds=duration,
                rtl_path=str(rtl_path),
                testbench_path=str(testbench_path),
                executable_path=str(executable_path),
                error_summary=(
                    None
                    if success
                    else self._summarize_simulation_error(
                        simulation_result.stdout or "",
                        simulation_result.stderr or "",
                    )
                ),
            )

    # ------------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------------

    def _validate_inputs(
        self,
        *,
        rtl_source: str,
        testbench_source: str,
        module_name: str,
    ) -> None:
        """Validate simulator inputs before touching the filesystem."""

        if not rtl_source.strip():
            raise SimulationError(
                "RTL source cannot be empty."
            )

        if not testbench_source.strip():
            raise SimulationError(
                "Testbench source cannot be empty."
            )

        if not module_name.strip():
            raise SimulationError(
                "Module name cannot be empty."
            )

        if len(rtl_source) > settings.max_rtl_length:
            raise SimulationError(
                "RTL source exceeds the configured size limit."
            )

        if len(testbench_source) > settings.max_testbench_output_length:
            raise SimulationError(
                "Testbench source exceeds the configured size limit."
            )

    # ------------------------------------------------------------------------
    # Locate Icarus
    # ------------------------------------------------------------------------

    def _find_simulator(self) -> str:
        """
        Resolve the Icarus Verilog executable.
        """

        if self._resolved_binary is not None:
            return self._resolved_binary

        candidates = [
            self.simulator_binary,
        ]

        if os.name == "nt":
            if not self.simulator_binary.lower().endswith(".exe"):
                candidates.append(
                    f"{self.simulator_binary}.exe"
                )

            # Local Windows Icarus installation.
            candidates.append(
                r"C:\iverilog\bin\iverilog.exe"
            )

        for candidate in candidates:

            # PATH lookup
            resolved = shutil.which(candidate)

            if resolved:
                self._resolved_binary = resolved
                return resolved

            # Direct filesystem lookup
            if os.path.isfile(candidate):
                self._resolved_binary = candidate
                return candidate

        raise SimulatorNotFoundError(
            "Icarus Verilog was not found. "
            "Install Icarus Verilog and ensure 'iverilog' "
            "is available on PATH."
        )

    # ------------------------------------------------------------------------
    # Compilation
    # ------------------------------------------------------------------------

    def _compile(
        self,
        *,
        binary: str,
        rtl_path: Path,
        testbench_path: Path,
        executable_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        """
        Compile RTL and testbench with Icarus Verilog.
        """

        command = [
            binary,

            # SystemVerilog mode.
            "-g2012",

            # Output executable.
            "-o",
            str(executable_path),

            # RTL.
            str(rtl_path),

            # Testbench.
            str(testbench_path),
        ]

        try:

            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=str(rtl_path.parent),
                check=False,
            )

        except subprocess.TimeoutExpired as exc:

            raise SimulationTimeoutError(
                "Icarus compilation exceeded the configured timeout."
            ) from exc

        except OSError as exc:

            raise SimulationError(
                f"Failed to execute Icarus Verilog: {exc}"
            ) from exc

    # ------------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------------

    def _simulate(
        self,
        *,
        executable_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        """
        Execute compiled Icarus simulation using vvp.
        """

        if not executable_path.exists():
            raise SimulationError(
                "Icarus compilation reported success, "
                "but no simulation executable was produced."
            )

        vvp_binary = shutil.which(
            "vvp"
        )

        if vvp_binary is None:

            # On some installations vvp is alongside iverilog.
            simulator_dir = Path(
                self._resolved_binary or ""
            ).parent

            candidate = (
                simulator_dir
                / (
                    "vvp.exe"
                    if os.name == "nt"
                    else "vvp"
                )
            )

            if candidate.exists():
                vvp_binary = str(candidate)

        if vvp_binary is None:
            raise SimulatorNotFoundError(
                "The 'vvp' runtime was not found. "
                "Install Icarus Verilog completely and ensure "
                "'vvp' is available on PATH."
            )

        command = [
            vvp_binary,
            str(executable_path),
        ]

        try:

            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=str(executable_path.parent),
                check=False,
            )

        except subprocess.TimeoutExpired:

            raise

        except OSError as exc:

            raise SimulationError(
                f"Failed to execute vvp simulation: {exc}"
            ) from exc

    # ------------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------------

    def _determine_status(
        self,
        *,
        return_code: int,
        stdout: str,
        stderr: str,
    ) -> str:
        """
        Determine the verification result.

        We intentionally inspect both:
            - process exit code
            - explicit testbench PASS/FAIL output

        This avoids considering a simulation successful merely because
        the simulator process exited with code 0.
        """

        combined_output = (
            f"{stdout}\n{stderr}"
        ).lower()

        # Explicit failure indicators have highest priority.
        failure_patterns = [
            r"\bFAIL\b",
            r"\bERROR\b",
            r"\bFAILED\b",
            r"\bFATAL\b",
            r"\bTEST\s+FAILED\b",
        ]

        for pattern in failure_patterns:

            if re.search(
                pattern,
                combined_output,
                flags=re.IGNORECASE,
            ):
                return "failed"

        # Non-zero process code means simulation failure.
        if return_code != 0:
            return "runtime_error"

        # Explicit PASS from our generated testbench.
        pass_patterns = [
            r"\bPASS\b",
            r"\bPASSED\b",
            r"\bTEST\s+PASSED\b",
            r"\bALL\s+TESTS\s+PASSED\b",
        ]

        for pattern in pass_patterns:

            if re.search(
                pattern,
                combined_output,
                flags=re.IGNORECASE,
            ):
                return "passed"

        # Simulation technically ran, but the testbench didn't provide
        # a clear verification result.
        return "unknown"

    # ------------------------------------------------------------------------
    # Compile error summary
    # ------------------------------------------------------------------------

    def _summarize_compile_error(
        self,
        stderr: str,
    ) -> str:
        """
        Convert compiler output into a concise summary.

        The complete compiler output is still returned to the caller.
        """

        if not stderr.strip():
            return "Icarus Verilog compilation failed."

        lines = [
            line.strip()
            for line in stderr.splitlines()
            if line.strip()
        ]

        # Icarus errors are usually already concise.
        if len(lines) <= 5:
            return " ".join(lines)

        return " ".join(lines[:5])

    # ------------------------------------------------------------------------
    # Simulation error summary
    # ------------------------------------------------------------------------

    def _summarize_simulation_error(
        self,
        stdout: str,
        stderr: str,
    ) -> str:
        """
        Produce a compact error summary while retaining full logs.
        """

        combined = [
            line.strip()
            for line in (
                f"{stdout}\n{stderr}"
            ).splitlines()
            if line.strip()
        ]

        if not combined:
            return "Simulation failed without diagnostic output."

        # Prefer lines containing error/fail/fatal.
        important = [
            line
            for line in combined
            if re.search(
                r"\b(error|fail|fatal|mismatch)\b",
                line,
                flags=re.IGNORECASE,
            )
        ]

        if important:
            return " ".join(important[:5])

        return " ".join(combined[:5])


# ============================================================================
# Shared simulator instance
# ============================================================================

simulator = IcarusSimulator()