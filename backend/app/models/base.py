from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from app.config.database import Base


class DataScopeType(str, Enum):
    """数据权限范围类型"""
    SELF = "self"                    # 仅本人数据
    DEPT = "dept"                    # 本部门数据
    DEPT_WITH_CHILD = "dept_with_child"  # 本部门及下级部门数据
    ALL = "all"                      # 全部数据


class BaseModel(Base):
    """基础模型，包含公共字段"""
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(10), default="active", comment="状态")
    del_flag: Mapped[str] = mapped_column(String(1), default="0", comment="删除标志(0存在 1删除)")
    create_by: Mapped[Optional[str]] = mapped_column(String(64), comment="创建者")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    update_by: Mapped[Optional[str]] = mapped_column(String(64), comment="更新者")
    update_time: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.now, comment="更新时间")