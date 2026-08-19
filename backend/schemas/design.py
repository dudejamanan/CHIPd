"""
Silica EDA Platform
===================

Pydantic schemas for design-related APIs.

A Design represents an individual hardware design inside a Project.

Design lifecycle:

    Specification
        ↓
    RTL Generation
        ↓
    Testbench Generation
        ↓
    Compilation
        ↓
    Simulation
        ↓
    Failure Analysis
        ↓
    AI RTL Repair
        ↓
    Re-verification
        ↓
    Verified Design
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================================
# Type aliases
# ============================================================================

HDLType = Literal[
    "systemverilog",
    "verilog",
]


DesignStatus = Literal[
    "draft",
    "generating",
    "generated",
    "verifying",
    "verified",
    "failed",
]


GenerationStatus = Literal[
    "generated",
    "failed",
]


# ============================================================================
# Design creation
# ============================================================================


class DesignCreate(BaseModel):
    """
    Request body for creating a hardware design.

    The specification remains natural language. The AI layer converts
    the specification into synthesizable RTL.
    """

    project_id: str = Field(
        ...,
        min_length=1,
        description="ID of the project that owns this design.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable design name.",
        examples=["4-bit Counter"],
    )

    specification: str = Field(
        ...,
        min_length=10,
        max_length=20_000,
        description=(
            "Natural-language hardware specification that "
            "Silica will translate into RTL."
        ),
        examples=[
            (
                "Create a synchronous 4-bit up counter with an "
                "active-low reset. The counter increments on every "
                "rising clock edge."
            )
        ],
    )

    hdl: HDLType = Field(
        default="systemverilog",
        description="Target hardware description language.",
    )

    module_name: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional preferred top-level RTL module name."
        ),
        examples=["counter_4bit"],
    )

    @field_validator("project_id")
    @classmethod
    def validate_project_id(
        cls,
        value: str,
    ) -> str:
        """Normalize project ID."""

        value = value.strip()

        if not value:
            raise ValueError(
                "Project ID cannot be empty."
            )

        return value

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        """Normalize and validate design name."""

        value = value.strip()

        if not value:
            raise ValueError(
                "Design name cannot be empty."
            )

        return value

    @field_validator("specification")
    @classmethod
    def validate_specification(
        cls,
        value: str,
    ) -> str:
        """Normalize and validate hardware specification."""

        value = value.strip()

        if len(value) < 10:
            raise ValueError(
                "Hardware specification is too short. "
                "Please provide enough detail to describe "
                "the intended hardware behavior."
            )

        return value

    @field_validator("module_name")
    @classmethod
    def validate_module_name(
        cls,
        value: str | None,
    ) -> str | None:
        """Validate optional Verilog/SystemVerilog module name."""

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not (
            value[0].isalpha()
            or value[0] == "_"
        ):
            raise ValueError(
                "Module name must begin with a letter or underscore."
            )

        if not all(
            character.isalnum() or character == "_"
            for character in value
        ):
            raise ValueError(
                "Module name may only contain letters, numbers, "
                "and underscores."
            )

        return value


# ============================================================================
# Design update
# ============================================================================


class DesignUpdate(BaseModel):
    """
    Request body for updating an existing design.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    specification: str | None = Field(
        default=None,
        min_length=10,
        max_length=20_000,
    )

    hdl: HDLType | None = None

    module_name: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize design name."""

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Design name cannot be empty."
            )

        return value

    @field_validator("specification")
    @classmethod
    def validate_specification(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize hardware specification."""

        if value is None:
            return None

        value = value.strip()

        if len(value) < 10:
            raise ValueError(
                "Hardware specification is too short."
            )

        return value

    @field_validator("module_name")
    @classmethod
    def validate_module_name(
        cls,
        value: str | None,
    ) -> str | None:
        """Validate optional module name."""

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not (
            value[0].isalpha()
            or value[0] == "_"
        ):
            raise ValueError(
                "Module name must begin with a letter or underscore."
            )

        if not all(
            character.isalnum() or character == "_"
            for character in value
        ):
            raise ValueError(
                "Module name may only contain letters, numbers, "
                "and underscores."
            )

        return value


# ============================================================================
# RTL generation
# ============================================================================


class RTLGenerationRequest(BaseModel):
    """
    Request to generate RTL from a natural-language specification.
    """

    specification: str = Field(
        ...,
        min_length=10,
        max_length=20_000,
        description="Natural-language hardware specification.",
        examples=[
            (
                "Create a 4-bit synchronous counter with an "
                "active-low reset."
            )
        ],
    )

    hdl: HDLType = Field(
        default="systemverilog",
        description="Target HDL.",
    )

    module_name: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional preferred top-level module name."
        ),
        examples=["counter_4bit"],
    )

    project_id: str | None = Field(
        default=None,
        description="Optional project to associate with the generated RTL.",
    )

    design_id: str | None = Field(
        default=None,
        description="Optional design to associate with the generated RTL.",
    )

    @field_validator("specification")
    @classmethod
    def validate_specification(
        cls,
        value: str,
    ) -> str:
        """Normalize specification."""

        value = value.strip()

        if len(value) < 10:
            raise ValueError(
                "Specification must contain at least 10 characters."
            )

        return value

    @field_validator(
        "module_name",
        "project_id",
        "design_id",
    )
    @classmethod
    def validate_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize optional identifiers."""

        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator("module_name")
    @classmethod
    def validate_module_name(
        cls,
        value: str | None,
    ) -> str | None:
        """Validate optional module name."""

        if value is None:
            return None

        if not (
            value[0].isalpha()
            or value[0] == "_"
        ):
            raise ValueError(
                "Module name must begin with a letter or underscore."
            )

        if not all(
            character.isalnum() or character == "_"
            for character in value
        ):
            raise ValueError(
                "Module name may only contain letters, numbers, "
                "and underscores."
            )

        return value


# ============================================================================
# RTL generation response
# ============================================================================


class RTLGenerationResponse(BaseModel):
    """
    Result returned by the RTL generation service.
    """

    design_id: str | None = None

    module_name: str

    hdl: HDLType

    rtl_source: str

    generation_status: GenerationStatus

    message: str | None = None

    model: str | None = None


# ============================================================================
# Testbench generation
# ============================================================================


class TestbenchGenerationRequest(BaseModel):
    """
    Request to generate a testbench for generated RTL.

    The actual RTL is supplied explicitly so the AI generates a testbench
    against the real design rather than an imagined interface.
    """

    rtl_source: str = Field(
        ...,
        min_length=10,
        max_length=100_000,
        description="Generated RTL source code.",
    )

    specification: str = Field(
        ...,
        min_length=10,
        max_length=20_000,
        description="Original hardware specification.",
    )

    module_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Top-level RTL module name.",
    )

    hdl: HDLType = Field(
        default="systemverilog",
    )

    design_id: str | None = None

    @field_validator("rtl_source")
    @classmethod
    def validate_rtl(
        cls,
        value: str,
    ) -> str:
        """Ensure RTL is not empty."""

        value = value.strip()

        if not value:
            raise ValueError(
                "RTL source cannot be empty."
            )

        return value

    @field_validator("specification")
    @classmethod
    def validate_specification(
        cls,
        value: str,
    ) -> str:
        """Normalize specification."""

        value = value.strip()

        if len(value) < 10:
            raise ValueError(
                "Specification is too short."
            )

        return value

    @field_validator("module_name")
    @classmethod
    def validate_module_name(
        cls,
        value: str,
    ) -> str:
        """Normalize module name."""

        value = value.strip()

        if not value:
            raise ValueError(
                "Module name cannot be empty."
            )

        return value


# ============================================================================
# Testbench generation response
# ============================================================================


class TestbenchGenerationResponse(BaseModel):
    """
    Result returned by testbench generation.
    """

    design_id: str | None = None

    module_name: str

    testbench_source: str

    generation_status: GenerationStatus

    message: str | None = None

    model: str | None = None


# ============================================================================
# Source response
# ============================================================================


class DesignSourceResponse(BaseModel):
    """
    Source-code response for a design.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    design_id: str

    module_name: str | None

    hdl: HDLType

    rtl_source: str | None

    testbench_source: str | None


# ============================================================================
# Design response
# ============================================================================


class DesignResponse(BaseModel):
    """
    Public representation of a hardware design.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    project_id: str

    name: str

    specification: str

    hdl: HDLType

    module_name: str | None

    rtl_source: str | None

    testbench_source: str | None

    status: DesignStatus

    verification_status: str | None = None

    verification_message: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================================
# Design list response
# ============================================================================


class DesignListResponse(BaseModel):
    """
    Paginated design list.
    """

    items: list[DesignResponse]

    total: int

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    pages: int = Field(
        default=1,
        ge=0,
    )