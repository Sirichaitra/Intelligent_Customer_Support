
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, Message

router = APIRouter(prefix="/api/history", tags=["History"])


class ConversationCreate(BaseModel):
    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=200,
    )


def serialize_message(message: Message):
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "sources": message.sources or [],
        "supported": message.supported,
        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        ),
    }


def serialize_conversation(conversation: Conversation):
    return {
        "id": conversation.id,
        "title": conversation.title,
        "document_filename": conversation.document_filename,
        "document_ready": conversation.document_ready,
        "created_at": (
            conversation.created_at.isoformat()
            if conversation.created_at
            else None
        ),
        "updated_at": (
            conversation.updated_at.isoformat()
            if conversation.updated_at
            else None
        ),
    }


@router.post("")
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
):
    conversation = Conversation(title=payload.title.strip())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return serialize_conversation(conversation)


@router.get("")
def list_conversations(
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    results = []

    for conversation in conversations:
        item = serialize_conversation(conversation)
        item["message_count"] = len(conversation.messages)

        last_message = (
            conversation.messages[-1]
            if conversation.messages
            else None
        )

        item["last_message"] = (
            last_message.content[:100]
            if last_message
            else ""
        )

        results.append(item)

    return {"conversations": results}


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    result = serialize_conversation(conversation)
    result["messages"] = [
        serialize_message(message)
        for message in conversation.messages
    ]

    return result


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }
