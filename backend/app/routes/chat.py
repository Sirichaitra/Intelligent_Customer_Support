
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.rag_services import answer_question


router = APIRouter(tags=["Chat"])


# --------------------------------------------------
# Request schema
# --------------------------------------------------

class AskRequest(BaseModel):
    conversation_id: int = Field(..., gt=0)
    question: str = Field(..., min_length=1, max_length=5000)


# --------------------------------------------------
# Ask a question
# --------------------------------------------------

@router.post("/api/ask")
def ask_question(
    payload: AskRequest,
    db: Session = Depends(get_db),
):
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # 1. Find the requested conversation.
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == payload.conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Conversation {payload.conversation_id} does not exist. "
                "Create a conversation and upload a document first."
            ),
        )

    # 2. Save the user's question.
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=question,
        sources=[],
        supported=True,
    )

    try:
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save the user message.",
        ) from exc

    # 3. Retrieve document context and generate the answer.
    try:
        result = answer_question(
            question=question,
            conversation_id=str(conversation.id),
        )

        if not isinstance(result, dict) or "answer" not in result:
            raise RuntimeError(
                "RAG service returned an invalid response."
            )

        answer = str(result["answer"])
        sources = result.get("sources", [])
        supported = bool(result.get("supported", False))

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "No document index was found for this conversation. "
                "Upload the document again to this conversation."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Log the actual error in the backend terminal.
        print(f"[CHAT ERROR] {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=502,
            detail=(
                "The RAG service could not generate an answer. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    # 4. Save the assistant's answer.
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        sources=sources,
        supported=supported,
    )

    try:
        db.add(assistant_message)

        # Update the conversation's last activity time if available.
        if hasattr(conversation, "updated_at"):
            from datetime import datetime, timezone
            conversation.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(assistant_message)

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="The answer was generated but could not be saved.",
        ) from exc

    # 5. Return the answer to Swagger or the frontend.
    return {
        "conversation_id": conversation.id,
        "question": question,
        "answer": answer,
        "sources": sources,
        "supported": supported,
        "message_id": assistant_message.id,
    }
