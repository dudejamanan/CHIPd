"""

Silica EDA Platform

===================



End-to-end AI-assisted RTL verification and repair pipeline.



Pipeline

--------



    Hardware Specification

             |

             v

       RTL Generator

             |

             v

      Testbench Generator

             |

             v

       Icarus Verilog

             |

        +----+----+

        |         |

      PASS       FAIL

        |         |

        v         v

     Success   Log Parser

                   |

                   v

            Failure Analyzer

                   |

                   v

             RTL Repairer

                   |

                   v

             Icarus Verilog

                   |

             +-----+-----+

             |           |

           PASS         FAIL

             |           |

             v           v

         Verified     Retry / Stop



Important

---------

Gemini never determines verification success.



Only the actual compiler/simulator result can mark a design as verified.

"""



from __future__ import annotations


import re
import time

from dataclasses import asdict, dataclass, field

from enum import Enum

from typing import Any



from backend.config import settings



from backend.services.failure_analyzer import (

    FailureAnalysis,

    FailureAnalysisError,

    failure_analyzer,

)



from backend.services.log_parser import (

    DiagnosticReport,

    log_parser,

)



from backend.services.rtl_generator import (

    RTLGenerationError,

    rtl_generator,

)



from backend.services.rtl_repairer import (

    RTLRepairError,

    RTLRepairResult,

    rtl_repairer,

)



from backend.services.simulator import (

    SimulationResult,

    simulator,

)



from backend.services.testbench_generator import (

    TestbenchGenerationError,

    testbench_generator,

)





# ============================================================================

# Pipeline status

# ============================================================================
import logging


logger = logging.getLogger(__name__)

class PipelineStatus(str, Enum):

    """

    High-level pipeline states.

    """



    INITIALIZING = "initializing"



    GENERATING_RTL = "generating_rtl"



    GENERATING_TESTBENCH = "generating_testbench"



    COMPILING = "compiling"



    SIMULATING = "simulating"



    ANALYZING_FAILURE = "analyzing_failure"



    REPAIRING_RTL = "repairing_rtl"



    REVERIFYING = "reverifying"



    VERIFIED = "verified"



    FAILED = "failed"



    ERROR = "error"





# ============================================================================

# Verification attempt

# ============================================================================





@dataclass(slots=True)

class VerificationAttempt:

    """

    Represents one compile/simulation attempt.

    """



    attempt_number: int



    rtl_source: str



    status: str



    passed: bool



    compile_success: bool



    simulation_success: bool



    stdout: str



    stderr: str



    diagnostics: DiagnosticReport | None



    duration_ms: int



    failure_analysis: FailureAnalysis | None = None



    repair: RTLRepairResult | None = None



    def to_dict(self) -> dict[str, Any]:

        """Convert attempt into a JSON-compatible structure."""



        result = asdict(self)



        if self.diagnostics is not None:

            result["diagnostics"] = (

                self.diagnostics.to_dict()

            )



        return result





# ============================================================================

# Pipeline result

# ============================================================================





@dataclass(slots=True)

class VerificationPipelineResult:

    """

    Complete end-to-end verification result.

    """



    status: PipelineStatus



    specification: str



    rtl_source: str



    testbench_source: str



    verified: bool



    attempts: list[VerificationAttempt]



    total_attempts: int



    total_duration_ms: int



    final_message: str



    final_diagnostics: DiagnosticReport | None = None



    final_analysis: FailureAnalysis | None = None



    def to_dict(self) -> dict[str, Any]:

        """Convert complete pipeline result to JSON."""



        return {

            "status": self.status.value,

            "specification": self.specification,

            "rtl_source": self.rtl_source,

            "testbench_source": self.testbench_source,

            "verified": self.verified,

            "attempts": [

                attempt.to_dict()

                for attempt in self.attempts

            ],

            "total_attempts": self.total_attempts,

            "total_duration_ms": self.total_duration_ms,

            "final_message": self.final_message,

            "final_diagnostics": (

                self.final_diagnostics.to_dict()

                if self.final_diagnostics

                else None

            ),

            "final_analysis": (

                self.final_analysis.to_dict()

                if self.final_analysis

                else None

            ),

        }





# ============================================================================

# Pipeline error

# ============================================================================





class VerificationPipelineError(Exception):

    """Raised when the verification pipeline cannot continue."""





# ============================================================================

# Pipeline

# ============================================================================





class VerificationPipeline:

    """

    Coordinates generation, simulation, diagnosis and repair.

    """



    def __init__(self) -> None:



        self.max_repair_attempts = max(

            0,

            settings.max_repair_attempts,

        )



    # ------------------------------------------------------------------------

    # Main pipeline

    # ------------------------------------------------------------------------



    async def run(

        self,

        specification: str,

    ) -> VerificationPipelineResult:

        """

        Run the complete AI-assisted RTL verification pipeline.



        Parameters

        ----------

        specification:

            Natural-language hardware specification.



        Returns

        -------

        VerificationPipelineResult

        """



        started_at = time.perf_counter()



        specification = specification.strip()



        if not specification:

            raise VerificationPipelineError(

                "Hardware specification cannot be empty."

            )



        # --------------------------------------------------------------------

        # STEP 1: Generate RTL

        # --------------------------------------------------------------------



        try:



            rtl_source = (

                await self._generate_rtl(

                    specification

                )

            )



        except RTLGenerationError as exc:



            return self._error_result(

                specification=specification,

                message=(

                    "RTL generation failed: "

                    f"{exc}"

                ),

                started_at=started_at,

            )



        # --------------------------------------------------------------------

        # STEP 2: Generate testbench

        # --------------------------------------------------------------------



        try:



            testbench_source = (

                await self._generate_testbench(

                    specification=specification,

                    rtl_source=rtl_source,

                )

            )



        except TestbenchGenerationError as exc:



            return self._error_result(

                specification=specification,

                rtl_source=rtl_source,

                message=(

                    "Testbench generation failed: "

                    f"{exc}"

                ),

                started_at=started_at,

            )



        # --------------------------------------------------------------------

        # STEP 3+: Verify and optionally repair

        # --------------------------------------------------------------------



        return self._verify_with_repair(

            specification=specification,

            rtl_source=rtl_source,

            testbench_source=testbench_source,

            started_at=started_at,

        )



    # ------------------------------------------------------------------------

    # RTL generation

    # ------------------------------------------------------------------------



    async def _generate_rtl(

        self,

        specification: str,

    ) -> str:

        """

        Generate initial RTL using Gemini.

        """



        result = await rtl_generator.generate(

            specification=specification

        )



        return result.rtl_source

    # ------------------------------------------------------------------------

    # Testbench generation

    # ------------------------------------------------------------------------



    def _extract_module_name(self, rtl_source: str) -> str:

        """

        Extract the first SystemVerilog module name from generated RTL.

        """

        import re



        match = re.search(

            r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)",

            rtl_source,

        )



        if not match:

            raise VerificationPipelineError(

                "Could not determine module name from generated RTL."

            )



        return match.group(1)





    async def _generate_testbench(

        self,

        *,

        specification: str,

        rtl_source: str,

    ) -> str:

        """

        Generate a verification testbench for the generated RTL.

        """



        module_name = self._extract_module_name(rtl_source)



        return await testbench_generator.generate(

            specification=specification,

            rtl_source=rtl_source,

            module_name=module_name,

        )

    # ------------------------------------------------------------------------

    # Verify + repair

    # ------------------------------------------------------------------------



    def _verify_with_repair(

        self,

        *,

        specification: str,

        rtl_source: str,

        testbench_source: str,

        started_at: float,

    ) -> VerificationPipelineResult:

        """

        Verify initial RTL and perform bounded AI repair attempts.

        """



        attempts: list[

            VerificationAttempt

        ] = []



        current_rtl = rtl_source



        final_diagnostics: DiagnosticReport | None = None



        final_analysis: FailureAnalysis | None = None



        # --------------------------------------------------------------------

        # Initial verification + bounded repairs.

        #

        # Example with max_repair_attempts = 2:

        #

        # Attempt 1: original RTL

        # Attempt 2: repair #1

        # Attempt 3: repair #2

        # --------------------------------------------------------------------



        for attempt_number in range(

            1,

            self.max_repair_attempts + 2,

        ):



            is_initial_attempt = (

                attempt_number == 1

            )



            simulation = self._run_simulation(

                rtl_source=current_rtl,

                testbench_source=testbench_source,

            )



            diagnostics = self._parse_diagnostics(

                simulation

            )



            final_diagnostics = diagnostics



            attempt = VerificationAttempt(

                attempt_number=attempt_number,

                rtl_source=current_rtl,

                status=simulation.status,

                passed=simulation.success,
                compile_success=simulation.success,
                simulation_success=simulation.success,
                stdout=simulation.simulation_stdout,
                stderr=simulation.simulation_stderr,

                diagnostics=diagnostics,

                duration_ms=0.0,

            )



            # ----------------------------------------------------------------

            # SUCCESS

            # ----------------------------------------------------------------



            if simulation.success:



                attempts.append(

                    attempt

                )



                total_duration = self._duration_ms(

                    started_at

                )



                return VerificationPipelineResult(

                    status=PipelineStatus.VERIFIED,

                    specification=specification,

                    rtl_source=current_rtl,

                    testbench_source=testbench_source,

                    verified=True,

                    attempts=attempts,

                    total_attempts=len(attempts),

                    total_duration_ms=total_duration,

                    final_message=(

                        "RTL successfully compiled and "

                        "passed verification."

                    ),

                    final_diagnostics=diagnostics,

                    final_analysis=final_analysis,

                )



            # ----------------------------------------------------------------

            # FAILURE

            # ----------------------------------------------------------------



            attempts.append(

                attempt

            )



            # No more repair attempts available.

            if (

                attempt_number

                > self.max_repair_attempts

            ):

                break



            # ----------------------------------------------------------------

            # STEP 4: Analyze failure

            # ----------------------------------------------------------------



            try:



                analysis = (

                    failure_analyzer.analyze(

                        specification=specification,

                        rtl_source=current_rtl,

                        testbench_source=testbench_source,

                        status=simulation.status,

                        diagnostics=diagnostics,

                        raw_output=self._combined_output(

                            simulation

                        ),

                    )

                )



            except FailureAnalysisError as exc:



                attempt.failure_analysis = None



                return self._failed_result(

                    specification=specification,

                    rtl_source=current_rtl,

                    testbench_source=testbench_source,

                    attempts=attempts,

                    diagnostics=diagnostics,

                    analysis=None,

                    message=(

                        "Verification failed and AI failure "

                        f"analysis could not be completed: {exc}"

                    ),

                    started_at=started_at,

                )



            attempt.failure_analysis = analysis



            final_analysis = analysis



            # ----------------------------------------------------------------

            # If Gemini says it didn't fail, don't blindly repair.

            # ----------------------------------------------------------------



            if not analysis.failed:



                return self._failed_result(

                    specification=specification,

                    rtl_source=current_rtl,

                    testbench_source=testbench_source,

                    attempts=attempts,

                    diagnostics=diagnostics,

                    analysis=analysis,

                    message=(

                        "Verification failed, but the AI analysis "

                        "could not establish a reliable RTL failure."

                    ),

                    started_at=started_at,

                )



            # ----------------------------------------------------------------

            # STEP 5: Repair RTL

            # ----------------------------------------------------------------



            try:



                repair = rtl_repairer.repair(

                    specification=specification,

                    rtl_source=current_rtl,

                    testbench_source=testbench_source,

                    analysis=analysis,

                    raw_diagnostics=self._combined_output(

                        simulation

                    ),

                )



            except RTLRepairError as exc:



                return self._failed_result(

                    specification=specification,

                    rtl_source=current_rtl,

                    testbench_source=testbench_source,

                    attempts=attempts,

                    diagnostics=diagnostics,

                    analysis=analysis,

                    message=(

                        "Verification failed and AI repair "

                        f"could not be generated: {exc}"

                    ),

                    started_at=started_at,

                )



            attempt.repair = repair



            # ----------------------------------------------------------------

            # STEP 6: Guard against no-op repair

            # ----------------------------------------------------------------



            if self._normalize_code(

                repair.rtl_source

            ) == self._normalize_code(

                current_rtl

            ):



                return self._failed_result(

                    specification=specification,

                    rtl_source=current_rtl,

                    testbench_source=testbench_source,

                    attempts=attempts,

                    diagnostics=diagnostics,

                    analysis=analysis,

                    message=(

                        "AI generated a repair candidate, "

                        "but it was identical to the previous RTL."

                    ),

                    started_at=started_at,

                )



            # ----------------------------------------------------------------

            # Move candidate into next verification attempt.

            # ----------------------------------------------------------------



            current_rtl = repair.rtl_source



        # --------------------------------------------------------------------

        # Exhausted repair budget.

        # --------------------------------------------------------------------



        return self._failed_result(

            specification=specification,

            rtl_source=current_rtl,

            testbench_source=testbench_source,

            attempts=attempts,

            diagnostics=final_diagnostics,

            analysis=final_analysis,

            message=(

                "Verification did not pass within the "

                f"{self.max_repair_attempts} allowed repair attempt(s)."

            ),

            started_at=started_at,

        )



    # ------------------------------------------------------------------------

    # Simulator

    # ------------------------------------------------------------------------



    def _run_simulation(

        self,

        *,

        rtl_source: str,

        testbench_source: str,

    ) -> SimulationResult:

        """

        Run RTL + testbench through Icarus.

        """



        match = re.search(
            r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)",
            rtl_source,
        )

        if not match:
            raise RuntimeError(
                "Could not determine DUT module name from generated RTL."
            )

        module_name = match.group(1)

        logger.info(
            "Running Icarus simulation for DUT module: %s",
            module_name,
        )

        return simulator.run(
            rtl_source=rtl_source,
            testbench_source=testbench_source.testbench_source,
            module_name=module_name,
        )



    # ------------------------------------------------------------------------

    # Log parsing

    # ------------------------------------------------------------------------



    def _parse_diagnostics(

        self,

        simulation: SimulationResult,

    ) -> DiagnosticReport:

        """

        Parse compiler/simulation output.

        """



        output = self._combined_output(

            simulation

        )



        return log_parser.parse(

            output

        )



    # ------------------------------------------------------------------------

    # Combined simulator output

    # ------------------------------------------------------------------------

    def _combined_output(self, simulation) -> str:
        """
        Combine all available simulator output for diagnostics.
        """

        parts = []

        if simulation.compile_stdout:
            parts.append(simulation.compile_stdout)

        if simulation.compile_stderr:
            parts.append(simulation.compile_stderr)

        if simulation.simulation_stdout:
            parts.append(simulation.simulation_stdout)

        if simulation.simulation_stderr:
            parts.append(simulation.simulation_stderr)

        return "\n".join(parts)

    # ------------------------------------------------------------------------

    # Failed result

    # ------------------------------------------------------------------------



    def _failed_result(

        self,

        *,

        specification: str,

        rtl_source: str,

        testbench_source: str,

        attempts: list[VerificationAttempt],

        diagnostics: DiagnosticReport | None,

        analysis: FailureAnalysis | None,

        message: str,

        started_at: float,

    ) -> VerificationPipelineResult:

        """

        Build a standard failed pipeline response.

        """



        return VerificationPipelineResult(

            status=PipelineStatus.FAILED,

            specification=specification,

            rtl_source=rtl_source,

            testbench_source=testbench_source,

            verified=False,

            attempts=attempts,

            total_attempts=len(attempts),

            total_duration_ms=self._duration_ms(

                started_at

            ),

            final_message=message,

            final_diagnostics=diagnostics,

            final_analysis=analysis,

        )



    # ------------------------------------------------------------------------

    # Error result

    # ------------------------------------------------------------------------



    def _error_result(

        self,

        *,

        specification: str,

        message: str,

        started_at: float,

        rtl_source: str = "",

        testbench_source: str = "",

    ) -> VerificationPipelineResult:

        """

        Build a standard pipeline error response.

        """



        return VerificationPipelineResult(

            status=PipelineStatus.ERROR,

            specification=specification,

            rtl_source=rtl_source,

            testbench_source=testbench_source,

            verified=False,

            attempts=[],

            total_attempts=0,

            total_duration_ms=self._duration_ms(

                started_at

            ),

            final_message=message,

        )



    # ------------------------------------------------------------------------

    # Duration

    # ------------------------------------------------------------------------



    def _duration_ms(

        self,

        started_at: float,

    ) -> int:

        """Return elapsed milliseconds."""



        return int(

            (

                time.perf_counter()

                - started_at

            )

            * 1000

        )



    # ------------------------------------------------------------------------

    # Code normalization

    # ------------------------------------------------------------------------



    def _normalize_code(

        self,

        source: str,

    ) -> str:

        """

        Normalize RTL enough to detect obvious no-op repairs.



        This intentionally does not attempt semantic equivalence.

        """



        return "\n".join(

            line.strip()

            for line in source.splitlines()

            if line.strip()

            and not line.strip().startswith(

                "//"

            )

        )





# ============================================================================

# Shared pipeline instance

# ============================================================================



verification_pipeline = VerificationPipeline()