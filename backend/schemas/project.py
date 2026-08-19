"""
Silica EDA Platform
====================

Pydantic schemas for project-related APIs.

A Project is the top-level workspace containing one or more hardware
designs.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================================
# Project creation
# ============================================================================


class ProjectCreate(BaseModel):
    """
    Request body for creating a new hardware project.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Project name.",
        examples=[
            "AI Counter Design"
        ],
    )

    description: str = Field(
        default="",
        max_length=5_000,
        description="Project description.",
        examples=[
            (
                "AI-assisted RTL generation and verification "
                "for a 4-bit counter."
            )
        ],
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        """Normalize and validate project name."""

        value = value.strip()

        if not value:
            raise ValueError(
                "Project name cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str,
    ) -> str:
        """Normalize project description."""

        return value.strip()


# ============================================================================
# Project update
# ============================================================================


class ProjectUpdate(BaseModel):
    """
    Request body for updating a project.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    description: str | None = Field(
        default=None,
        max_length=5_000,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize project name."""

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Project name cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize project description."""

        if value is None:
            return None

        return value.strip()


# ============================================================================
# Project response
# ============================================================================


class ProjectResponse(BaseModel):
    """
    Public representation of a project.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    name: str

    description: str

    verification_status: str = "not_verified"

    verification_message: str | None = None

    created_at: datetime

    updated_at: datetime


# ============================================================================
# Project summary
# ============================================================================


class ProjectSummary(BaseModel):
    """
    Lightweight project representation for dashboards and navigation.

    This avoids loading large RTL/testbench source files when the frontend
    only needs project metadata.
    """

    id: str

    name: str

    description: str

    design_count: int = 0

    verification_status: str = "not_verified"

    updated_at: datetime


# ============================================================================
# Project list
# ============================================================================


class ProjectListResponse(BaseModel):
    """
    Paginated project list.
    """

    items: list[ProjectResponse]

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