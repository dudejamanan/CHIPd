"""
Database layer for Silica AI-assisted EDA Platform.

SQLite + SQLAlchemy 2.x
Designed for local development and hackathon MVP usage.

This module provides:
- Database initialization
- Project CRUD helpers
- Design CRUD helpers
- Verification result persistence
- Analysis result persistence
- Safe session management

No Docker or external database is required.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)


# ============================================================
# BASE
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# MODELS
# ============================================================

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    designs: Mapped[list["Design"]] = relationship(
        "Design",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Design(Base):
    __tablename__ = "designs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Untitled Design",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    rtl_source: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    testbench_source: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SystemVerilog",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="generated",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="designs",
    )

    verification_results: Mapped[list["VerificationResult"]] = relationship(
        "VerificationResult",
        back_populates="design",
        cascade="all, delete-orphan",
    )


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    design_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("designs.id", ondelete="CASCADE"),
        nullable=False,
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    compile_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    simulation_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    errors: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    warnings: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    design: Mapped["Design"] = relationship(
        "Design",
        back_populates="verification_results",
    )


# ============================================================
# ENGINE / SESSION
# ============================================================

_engine = None
_SessionLocal = None


def _normalize_database_url(database_url: str) -> str:
    """
    Normalize database URLs so SQLAlchemy can use them locally.

    Examples:
        sqlite:///./silica.db
        sqlite+aiosqlite:///./silica.db
    """

    if not database_url:
        database_url = "sqlite:///./silica.db"

    database_url = database_url.replace(
        "sqlite+aiosqlite://",
        "sqlite://",
    )

    return database_url


def get_engine(database_url: Optional[str] = None):
    """
    Create or return the SQLAlchemy engine.
    """

    global _engine

    if _engine is not None and database_url is None:
        return _engine

    if database_url is None:
        try:
            from backend.config import settings

            database_url = settings.database_url
        except Exception:
            database_url = "sqlite:///./silica.db"

    database_url = _normalize_database_url(database_url)

    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args = {
            "check_same_thread": False,
        }

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
    )

    if _engine is None:
        _engine = engine

    return engine


def get_session_factory():
    """
    Return the configured SQLAlchemy session factory.
    """

    global _SessionLocal

    if _SessionLocal is not None:
        return _SessionLocal

    engine = get_engine()

    _SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    return _SessionLocal


def get_db():
    """
    FastAPI dependency.

    Usage:

        db: Session = Depends(get_db)
    """

    SessionLocal = get_session_factory()

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Any, None, None]:
    """
    Context manager for service-layer database operations.
    """

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================
# INITIALIZATION
# ============================================================

def init_db(app=None):
    """
    Initialize database tables.

    Compatible with the FastAPI startup flow and also safe
    to call directly.
    """

    engine = get_engine()

    Base.metadata.create_all(bind=engine)

    return engine


# ============================================================
# PROJECT CRUD
# ============================================================

def create_project(
    name: str,
    description: Optional[str] = None,
) -> Project:
    """
    Create a new project.
    """

    with session_scope() as db:

        project = Project(
            name=name,
            description=description,
        )

        db.add(project)
        db.flush()

        db.refresh(project)

        return project


def get_project(
    project_id: str,
) -> Optional[Project]:
    """
    Get a project by ID.
    """

    with session_scope() as db:

        return db.scalar(
            select(Project).where(
                Project.id == project_id
            )
        )


def get_projects() -> list[Project]:
    """
    Return all projects ordered by newest first.
    """

    with session_scope() as db:

        return list(
            db.scalars(
                select(Project)
                .order_by(Project.created_at.desc())
            ).all()
        )


def list_projects() -> list[Project]:
    """
    Alias kept for compatibility.
    """

    return get_projects()


def update_project(
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Project]:
    """
    Update an existing project.
    """

    with session_scope() as db:

        project = db.scalar(
            select(Project).where(
                Project.id == project_id
            )
        )

        if project is None:
            return None

        if name is not None:
            project.name = name

        if description is not None:
            project.description = description

        project.updated_at = datetime.now(timezone.utc)

        db.flush()
        db.refresh(project)

        return project


def delete_project(
    project_id: str,
) -> bool:
    """
    Delete a project and its associated designs.
    """

    with session_scope() as db:

        project = db.scalar(
            select(Project).where(
                Project.id == project_id
            )
        )

        if project is None:
            return False

        db.delete(project)

        return True


# ============================================================
# DESIGN CRUD
# ============================================================

def create_design(
    name: str = "Untitled Design",
    description: Optional[str] = None,
    project_id: Optional[str] = None,
    rtl_source: Optional[str] = None,
    testbench_source: Optional[str] = None,
    language: str = "SystemVerilog",
    status: str = "generated",
) -> Design:
    """
    Persist a generated RTL design.
    """

    with session_scope() as db:

        design = Design(
            name=name,
            description=description,
            project_id=project_id,
            rtl_source=rtl_source,
            testbench_source=testbench_source,
            language=language,
            status=status,
        )

        db.add(design)
        db.flush()

        db.refresh(design)

        return design


def get_design(
    design_id: str,
) -> Optional[Design]:
    """
    Get a design by ID.
    """

    with session_scope() as db:

        return db.scalar(
            select(Design).where(
                Design.id == design_id
            )
        )


def get_designs(
    project_id: Optional[str] = None,
) -> list[Design]:
    """
    Get designs, optionally filtered by project.
    """

    with session_scope() as db:

        query = select(Design)

        if project_id:
            query = query.where(
                Design.project_id == project_id
            )

        query = query.order_by(
            Design.created_at.desc()
        )

        return list(
            db.scalars(query).all()
        )


def update_design(
    design_id: str,
    **fields: Any,
) -> Optional[Design]:
    """
    Update arbitrary safe Design fields.
    """

    allowed_fields = {
        "name",
        "description",
        "rtl_source",
        "testbench_source",
        "language",
        "status",
        "project_id",
    }

    with session_scope() as db:

        design = db.scalar(
            select(Design).where(
                Design.id == design_id
            )
        )

        if design is None:
            return None

        for key, value in fields.items():

            if key in allowed_fields:
                setattr(design, key, value)

        design.updated_at = datetime.now(timezone.utc)

        db.flush()
        db.refresh(design)

        return design


def delete_design(
    design_id: str,
) -> bool:
    """
    Delete a design.
    """

    with session_scope() as db:

        design = db.scalar(
            select(Design).where(
                Design.id == design_id
            )
        )

        if design is None:
            return False

        db.delete(design)

        return True


# ============================================================
# VERIFICATION CRUD
# ============================================================

def create_verification_result(
    design_id: str,
    passed: bool,
    compile_success: bool,
    simulation_success: bool,
    output: Optional[str] = None,
    errors: Optional[str] = None,
    warnings: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> VerificationResult:
    """
    Store a verification run.
    """

    with session_scope() as db:

        result = VerificationResult(
            design_id=design_id,
            passed=passed,
            compile_success=compile_success,
            simulation_success=simulation_success,
            output=output,
            errors=errors,
            warnings=warnings,
            duration_ms=duration_ms,
        )

        db.add(result)
        db.flush()

        db.refresh(result)

        return result


def get_verification_result(
    result_id: str,
) -> Optional[VerificationResult]:
    """
    Retrieve one verification result.
    """

    with session_scope() as db:

        return db.scalar(
            select(VerificationResult).where(
                VerificationResult.id == result_id
            )
        )


def get_verification_results(
    design_id: str,
) -> list[VerificationResult]:
    """
    Retrieve all verification runs for a design.
    """

    with session_scope() as db:

        return list(
            db.scalars(
                select(VerificationResult)
                .where(
                    VerificationResult.design_id == design_id
                )
                .order_by(
                    VerificationResult.created_at.desc()
                )
            ).all()
        )


# ============================================================
# SERIALIZATION HELPERS
# ============================================================

def project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": (
            project.created_at.isoformat()
            if project.created_at
            else None
        ),
        "updated_at": (
            project.updated_at.isoformat()
            if project.updated_at
            else None
        ),
    }


def design_to_dict(design: Design) -> dict:
    return {
        "id": design.id,
        "project_id": design.project_id,
        "name": design.name,
        "description": design.description,
        "rtl_source": design.rtl_source,
        "testbench_source": design.testbench_source,
        "language": design.language,
        "status": design.status,
        "created_at": (
            design.created_at.isoformat()
            if design.created_at
            else None
        ),
        "updated_at": (
            design.updated_at.isoformat()
            if design.updated_at
            else None
        ),
    }


def verification_to_dict(
    result: VerificationResult,
) -> dict:
    return {
        "id": result.id,
        "design_id": result.design_id,
        "passed": result.passed,
        "compile_success": result.compile_success,
        "simulation_success": result.simulation_success,
        "output": result.output,
        "errors": result.errors,
        "warnings": result.warnings,
        "duration_ms": result.duration_ms,
        "created_at": (
            result.created_at.isoformat()
            if result.created_at
            else None
        ),
    }


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

# Some of the existing service code may use these names.
ProjectModel = Project
DesignModel = Design
VerificationResultModel = VerificationResult