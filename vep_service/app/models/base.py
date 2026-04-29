"""Base Model for VEP Service

Simplified BaseModel WITHOUT user-related fields.
NO create_by, NO user_id - this is an open access service.
"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base


class BaseModel(Base):
    """
    Base model for VEP service tables.

    Simplified - NO user tracking fields (create_by, user_id).
    Open access service - annotations are shared globally.
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(10), default="active", comment="Status")
    del_flag: Mapped[str] = mapped_column(String(1), default="0", comment="Delete flag")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="Creation time")