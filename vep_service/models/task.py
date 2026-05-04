"""Task Tracking Model

Tracks asynchronous VEP annotation tasks for polling.
NO user_id - tasks are accessible by task_id only (no ownership check).
"""

import uuid
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import String, Integer, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from models.base import BaseModel


class VepTaskStatus(str, Enum):
    """VEP annotation task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class VepTask(BaseModel):
    """
    VEP annotation task tracking.

    NO user tracking - tasks accessible by task_id only.
    Public access - no ownership verification required.
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

    # NO user_id field - open access, public tasks