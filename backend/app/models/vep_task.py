"""VEP Task Tracking Model

Tracks asynchronous VEP annotation tasks for user polling.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
from sqlalchemy import String, Integer, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import UserModel


class VepTaskStatus(str, Enum):
    """VEP annotation task status"""
    PENDING = "pending"      # Task created, waiting to start
    RUNNING = "running"      # VEP annotation in progress
    COMPLETED = "completed"  # Annotation finished successfully
    FAILED = "failed"        # Annotation failed with error


class VepTask(BaseModel):
    """
    VEP annotation task tracking

    Stores task metadata for asynchronous annotation processing.
    Users poll task status to retrieve results when ready.
    """
    __tablename__ = "vep_task"

    # Task identification
    task_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique task identifier (UUID)"
    )

    # Task state
    task_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=VepTaskStatus.PENDING.value,
        index=True,
        comment="Task status (pending/running/completed/failed)"
    )

    # Input data
    input_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Original annotation request (variants list)"
    )

    # Annotation configuration
    species: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Genome assembly used (GRCh37, GRCh38)"
    )
    mode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Annotation mode (sync/async)"
    )

    # Results
    result_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of annotated variants"
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if task failed"
    )

    # Timestamps for task lifecycle
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Time when VEP processing started"
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Time when VEP processing completed"
    )

    # User ownership
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sys_user.id"),
        nullable=True,
        index=True,
        comment="User who submitted the annotation request"
    )

    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship(
        foreign_keys=[user_id]
    )