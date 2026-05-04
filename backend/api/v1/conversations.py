"""Conversation API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List
import json
import logging

from api.deps import get_db, get_current_user
from models import UserModel, ConversationModel, MessageModel, MessageRole
from schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
)
from services.llm import generate_chat_with_tools

router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[ConversationListResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """List all conversations for current user"""
    result = await db.execute(
        select(ConversationModel)
        .where(
            ConversationModel.user_id == current_user.id,
            ConversationModel.del_flag == "0"
        )
        .order_by(ConversationModel.last_message_at.desc().nullslast())
    )
    conversations = result.scalars().all()
    return conversations


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new conversation"""
    conversation = ConversationModel(
        user_id=current_user.id,
        title=request.title,
        model=request.model,
        is_archived=False,
        del_flag="0"
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get conversation with messages"""
    result = await db.execute(
        select(ConversationModel)
        .options(selectinload(ConversationModel.messages))
        .where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == current_user.id,
            ConversationModel.del_flag == "0"
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update conversation"""
    result = await db.execute(
        select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == current_user.id,
            ConversationModel.del_flag == "0"
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if request.title is not None:
        conversation.title = request.title
    if request.is_archived is not None:
        conversation.is_archived = request.is_archived

    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete conversation (soft delete)"""
    result = await db.execute(
        select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == current_user.id,
            ConversationModel.del_flag == "0"
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    conversation.del_flag = "1"
    await db.commit()

    return {"message": "Conversation deleted"}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    request: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Send a message and get streaming response"""

    # Verify conversation exists
    result = await db.execute(
        select(ConversationModel)
        .options(selectinload(ConversationModel.messages))
        .where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == current_user.id,
            ConversationModel.del_flag == "0"
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Save user message
    user_message = MessageModel(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.content,
    )
    db.add(user_message)
    await db.commit()

    # Update conversation timestamp
    conversation.last_message_at = datetime.now(timezone.utc)

    # Get conversation history
    messages = [
        {"role": msg.role.value, "content": msg.content}
        for msg in conversation.messages
    ]
    messages.append({"role": "user", "content": request.content})

    async def generate():
        """Generate streaming response"""
        chunks = []

        try:
            # Stream response from LLM
            async for chunk in generate_chat_with_tools(messages, model=conversation.model):
                chunks.append(chunk)
                # SSE format
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # Save assistant message
            assistant_content = "".join(chunks)
            assistant_message = MessageModel(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
            )
            db.add(assistant_message)
            await db.commit()

            # Send done signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("LLM streaming error in conversation %d", conversation_id)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )