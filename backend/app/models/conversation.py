from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.config import settings
from app.models.base import BaseModel


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationModel(BaseModel):
    """对话表"""
    __tablename__ = "conversations"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_user.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    title: Mapped[str] = mapped_column(String(255), default="新对话", comment="对话标题")
    model: Mapped[str] = mapped_column(String(50), default=settings.CONVERSATION_DEFAULT_MODEL, comment="使用的LLM模型")
    is_archived: Mapped[bool] = mapped_column(default=False, comment="是否归档")
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="最后消息时间"
    )

    # 关系
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id])
    messages: Mapped[list["MessageModel"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AnalysisModel"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class MessageModel(BaseModel):
    """消息表"""
    __tablename__ = "messages"

    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="对话ID"
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole),
        nullable=False,
        comment="消息角色"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, comment="元数据(分析参数等)")

    # 关系
    conversation: Mapped["ConversationModel"] = relationship(back_populates="messages")