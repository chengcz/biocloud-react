"""Pydantic schemas for conversations"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from config import settings


class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: Optional[str] = Field(default="新对话", max_length=255)
    model: Optional[str] = Field(default=settings.CONVERSATION_DEFAULT_MODEL, max_length=50)


class ConversationCreate(ConversationBase):
    """Conversation creation schema"""
    pass


class ConversationUpdate(BaseModel):
    """Conversation update schema"""
    title: Optional[str] = Field(None, max_length=255)
    is_archived: Optional[bool] = None


class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(..., min_length=1, max_length=10000)


class MessageCreate(MessageBase):
    """Message creation schema"""
    role: str = Field(default="user", pattern="^(user|system)$")


class MessageResponse(BaseModel):
    """Message response schema"""
    id: int
    conversation_id: int
    role: str
    content: str
    metadata: Optional[dict] = None
    create_time: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response schema"""
    id: int
    user_id: int
    title: str
    model: str
    is_archived: bool
    last_message_at: Optional[datetime] = None
    create_time: datetime
    messages: Optional[List[MessageResponse]] = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Conversation list response (without messages)"""
    id: int
    user_id: int
    title: str
    model: str
    is_archived: bool
    last_message_at: Optional[datetime] = None
    create_time: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None
    stream: bool = True


class IntentResult(BaseModel):
    """Intent detection result"""
    intent: str
    confidence: float
    parameters: dict = Field(default_factory=dict)
    analysis_type: Optional[str] = None