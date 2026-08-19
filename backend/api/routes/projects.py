"""
Silica EDA Platform
====================

Project management API.

A project represents a hardware-design workspace.

For the MVP, a project stores:
    - name
    - description
    - current RTL
    - current testbench
    - verification status

The route layer stays thin. Database/application logic belongs in the
appropriate service/model layers.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.models.database import (
    create_project,
    get_project,
    list_projects,
)

from backend.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectSummary,
)

# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    tags=["Projects"],
)


# ============================================================================
# Request models
# ============================================================================


class ProjectCreateRequest(BaseModel):
    """
    Create a new hardware design project.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Project name.",
        examples=[
            "4-bit Counter"
        ],
    )

    description: str = Field(
        default="",
        max_length=5_000,
        description="Optional project description.",
        examples=[
            "AI-assisted 4-bit synchronous counter design."
        ],
    )


# ============================================================================
# Response models
# ============================================================================


class ProjectResponse(BaseModel):
    """
    Public representation of a project.
    """

    id: str

    name: str

    description: str

    rtl_source: str | None = None

    testbench_source: str | None = None

    verification_status: str

    created_at: str | None = None

    updated_at: str | None = None


class ProjectListResponse(BaseModel):
    """
    Project listing response.
    """

    projects: list[ProjectResponse]

    total: int


# ============================================================================
# Helpers
# ============================================================================


def _project_to_response(
    project: Any,
) -> ProjectResponse:
    """
    Convert a database project object into an API response.

    Supports both ORM-style objects and dictionary-like objects. This makes
    the route resilient while the database layer is still evolving.
    """

    def read(
        key: str,
        default: Any = None,
    ) -> Any:

        if isinstance(
            project,
            dict,
        ):

            return project.get(
                key,
                default,
            )

        return getattr(
            project,
            key,
            default,
        )

    created_at = read(
        "created_at"
    )

    updated_at = read(
        "updated_at"
    )

    return ProjectResponse(
        id=str(
            read(
                "id",
                "",
            )
        ),
        name=str(
            read(
                "name",
                "",
            )
        ),
        description=str(
            read(
                "description",
                "",
            )
        ),
        rtl_source=read(
            "rtl_source"
        ),
        testbench_source=read(
            "testbench_source"
        ),
        verification_status=str(
            read(
                "verification_status",
                "not_verified",
            )
        ),
        created_at=(
            created_at.isoformat()
            if hasattr(
                created_at,
                "isoformat",
            )
            else (
                str(created_at)
                if created_at is not None
                else None
            )
        ),
        updated_at=(
            updated_at.isoformat()
            if hasattr(
                updated_at,
                "isoformat",
            )
            else (
                str(updated_at)
                if updated_at is not None
                else None
            )
        ),
    )


# ============================================================================
# Project routes
# ============================================================================


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List hardware design projects",
)
async def list_all_projects() -> ProjectListResponse:
    """
    Return all projects.

    This endpoint is intentionally simple for the MVP. Pagination can be
    introduced later when project counts become large.
    """

    try:

        projects = list_projects()

    except Exception as exc:

        logger.exception(
            "Failed to list projects."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load projects.",
        ) from exc

    responses = [
        _project_to_response(
            project
        )
        for project in projects
    ]

    return ProjectListResponse(
        projects=responses,
        total=len(responses),
    )


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a hardware design project",
)
async def create_new_project(
    request: ProjectCreateRequest,
) -> ProjectResponse:
    """
    Create a new hardware design project.
    """

    name = request.name.strip()

    description = request.description.strip()

    if not name:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name cannot be empty.",
        )

    try:

        project = create_project(
            name=name,
            description=description,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception(
            "Failed to create project."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project.",
        ) from exc

    return _project_to_response(
        project
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a hardware design project",
)
async def get_project_by_id(
    project_id: str,
) -> ProjectResponse:
    """
    Retrieve a single project.
    """

    if not project_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID is required.",
        )

    try:

        project = get_project(
            project_id
        )

    except Exception as exc:

        logger.exception(
            "Failed to retrieve project %s.",
            project_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project.",
        ) from exc

    if project is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Project '{project_id}' was not found."
            ),
        )

    return _project_to_response(
        project
    )