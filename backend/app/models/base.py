#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional, AsyncGenerator

from enum import Enum
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


from app.config import settings



# Create async engine (SQLite doesn't support pool_size)
engine_args = {"echo": settings.DEBUG}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_args.update({"pool_size": 10, "max_overflow": 20})

engine = create_async_engine(settings.DATABASE_URL, **engine_args)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


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
