"""

Silica EDA Platform

===================



Central application configuration.



All environment-dependent configuration lives here.



For the SIH MVP:

    - Gemini is used as the LLM

    - SQLite is used as the local database

    - Icarus Verilog is used for RTL simulation

    - No Docker

    - No external database

"""



from __future__ import annotations



from pathlib import Path

from typing import List



from pydantic import Field, field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict





# ============================================================================

# Paths

# ============================================================================



PROJECT_ROOT = Path(__file__).resolve().parents[1]



BACKEND_DIR = PROJECT_ROOT / "backend"



WORKSPACE_DIR = PROJECT_ROOT / "workspace"



DATA_DIR = PROJECT_ROOT / "data"



PROMPTS_DIR = BACKEND_DIR / "prompts"





# Make sure important local directories exist.

WORKSPACE_DIR.mkdir(

    parents=True,

    exist_ok=True,

)



DATA_DIR.mkdir(

    parents=True,

    exist_ok=True,

)





# ============================================================================

# Settings

# ============================================================================





class Settings(BaseSettings):

    """

    Application configuration loaded from environment variables.



    Environment variables can be defined in:



        .env



    Example:



        GEMINI_API_KEY=your_key_here

        APP_HOST=127.0.0.1

        APP_PORT=8000

    """



    model_config = SettingsConfigDict(

        env_file=".env",

        env_file_encoding="utf-8",

        case_sensitive=False,

        extra="ignore",

    )



    # ------------------------------------------------------------------------

    # Application

    # ------------------------------------------------------------------------



    app_name: str = Field(

        default="Silica",

        description="Application name.",

    )



    app_version: str = Field(

        default="0.1.0",

        description="Application version.",

    )



    app_host: str = Field(

        default="127.0.0.1",

        description="Local API host.",

    )



    app_port: int = Field(

        default=8000,

        ge=1,

        le=65535,

        description="FastAPI port.",

    )



    debug: bool = Field(

        default=True,

        description="Enable development debugging.",

    )

    # ============================================================================

    # HDL Simulation

    # ============================================================================



    simulator: str = "icarus"



    # ------------------------------------------------------------------------

    # Gemini

    # ------------------------------------------------------------------------

# ============================================================================

# RTL / Verification limits

# ============================================================================



    max_rtl_length: int = 50_000



    # Used by RTL generator validation.

    max_rtl_output_length: int = 50_000



    # Maximum context sent to the failure-analysis LLM.

    max_analysis_context_length: int = 30_000

# ------------------------------------------------------------------------

# LLM

# ------------------------------------------------------------------------



    groq_api_key: str = Field(

        default="",

        description="Groq API key.",

    )



    groq_model: str = Field(
        default="openai/gpt-oss-20b",
        description="Groq model used by the AI pipeline.",
    )



    llm_temperature: float = Field(

        default=0.2,

        ge=0.0,

        le=2.0,

        description="LLM generation temperature.",

    )



    llm_max_output_tokens: int = Field(

        default=2048,

        ge=256,

        description="Maximum LLM output tokens.",

    )



    llm_timeout_seconds: int = Field(

        default=120,

        ge=10,

        description="LLM request timeout.",

    )

    # ------------------------------------------------------------------------

    # Database

    # ------------------------------------------------------------------------



    database_url: str = Field(

        default="sqlite:///./data/silica.db",

        description="SQLAlchemy database URL.",

    )



    # ------------------------------------------------------------------------

    # CORS

    # ------------------------------------------------------------------------



    cors_origins: List[str] = Field(

        default=[

            "http://localhost:3000",

            "http://127.0.0.1:3000",

        ],

        description="Allowed frontend origins.",

    )



    # ------------------------------------------------------------------------

    # Workspace

    # ------------------------------------------------------------------------



    workspace_dir: str = Field(

        default=str(WORKSPACE_DIR),

        description="Directory where generated HDL artifacts are stored.",

    )



    # ------------------------------------------------------------------------

    # RTL generation

    # ------------------------------------------------------------------------



    max_rtl_context_length: int = Field(

        default=20000,

        ge=1000,

        description="Maximum context passed to RTL generation.",

    )



    max_rtl_output_length: int = Field(

        default=50000,

        ge=1000,

        description="Maximum accepted generated RTL length.",

    )



    # ------------------------------------------------------------------------

    # Testbench generation

    # ------------------------------------------------------------------------



    max_testbench_context_length: int = Field(

        default=30000,

        ge=1000,

        description="Maximum context passed to testbench generation.",

    )



    max_testbench_output_length: int = Field(

        default=50000,

        ge=1000,

        description="Maximum accepted testbench length.",

    )



    # ------------------------------------------------------------------------

    # Failure analysis

    # ------------------------------------------------------------------------



    max_analysis_context_length: int = Field(

        default=12000,

        ge=1000,

        description=(

            "Maximum compiler/simulation context passed to Gemini "

            "during failure analysis."

        ),

    )



    max_analysis_output_length: int = Field(

        default=12000,

        ge=1000,

        description="Maximum accepted failure-analysis response.",

    )



    # ------------------------------------------------------------------------

    # RTL repair

    # ------------------------------------------------------------------------



    max_repair_context_length: int = Field(

        default=30000,

        ge=1000,

        description="Maximum context passed to Gemini for RTL repair.",

    )



    max_repair_output_length: int = Field(

        default=50000,

        ge=1000,

        description="Maximum accepted repaired RTL length.",

    )



    # ------------------------------------------------------------------------

    # Simulation

    # ------------------------------------------------------------------------



    simulator_command: str = Field(

        default="iverilog",

        description="Icarus Verilog executable.",

    )



    vvp_command: str = Field(

        default="vvp",

        description="Icarus VVP executable.",

    )



    simulation_timeout_seconds: int = Field(

        default=15,

        ge=1,

        description="Maximum simulation execution time.",

    )



    compilation_timeout_seconds: int = Field(

        default=15,

        ge=1,

        description="Maximum RTL compilation time.",

    )



    # ------------------------------------------------------------------------

    # Verification

    # ------------------------------------------------------------------------



    max_repair_attempts: int = Field(

        default=3,

        ge=0,

        le=10,

        description=(

            "Maximum number of automatic AI repair attempts "

            "after verification failure."

        ),

    )



    verification_timeout_seconds: int = Field(

        default=60,

        ge=5,

        description="Maximum total verification time.",

    )



    # ------------------------------------------------------------------------

    # Logging

    # ------------------------------------------------------------------------



    log_level: str = Field(

        default="INFO",

        description="Application log level.",

    )



    # ------------------------------------------------------------------------

    # Validators

    # ------------------------------------------------------------------------



    @field_validator("cors_origins", mode="before")

    @classmethod

    def parse_cors_origins(

        cls,

        value,

    ):

        """

        Allow either:



            CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000



        or a normal list.

        """



        if isinstance(value, str):

            return [

                origin.strip()

                for origin in value.split(",")

                if origin.strip()

            ]



        return value



    @field_validator("log_level")

    @classmethod

    def normalize_log_level(

        cls,

        value: str,

    ) -> str:

        """Normalize logging level."""



        value = value.strip().upper()



        allowed = {

            "DEBUG",

            "INFO",

            "WARNING",

            "ERROR",

            "CRITICAL",

        }



        if value not in allowed:

            raise ValueError(

                f"Invalid log level: {value}"

            )



        return value



    # ------------------------------------------------------------------------

    # Helpers

    # ------------------------------------------------------------------------



    @property

    def workspace_path(self) -> Path:

        """Return workspace directory as a Path."""



        path = Path(self.workspace_dir)



        path.mkdir(

            parents=True,

            exist_ok=True,

        )



        return path



    @property

    def prompts_path(self) -> Path:

        """Return prompt directory."""



        return PROMPTS_DIR





    @property

    def is_llm_configured(self) -> bool:

        """Return whether the Groq API credentials are configured."""

        return bool(

            self.groq_api_key

            and self.groq_api_key.strip()

        )



# ============================================================================

# Global settings instance

# ============================================================================



settings = Settings()

