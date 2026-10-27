
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation
from app.services.document_rag import process_document

router = APIRouter(prefix="/api", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a document.",
        )

    filename = file.filename
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT, and DOCX files are supported.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded document is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum document size is 10 MB.",
        )

    if conversation_id is None:
        conversation = Conversation(
            title=f"Product inquiry: {filename}",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    else:
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

    try:
        # IMPORTANT:
        # document_rag.py must support a separate index per conversation.
        result = process_document(
            filename,
            content,
            conversation_id=str(conversation.id),
        )
    except TypeError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The RAG service must accept conversation_id and maintain "
                "a separate vector index per conversation. Update "
                "document_rag.py before using this endpoint."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not process the document: {exc}",
        ) from exc

    conversation.document_filename = filename
    conversation.document_ready = True

    if conversation.title == "New conversation":
        conversation.title = f"Product inquiry: {filename}"

    db.commit()
    db.refresh(conversation)

    chunks = None
    if isinstance(result, dict):
        chunks = result.get("chunks") or result.get("chunk_count")

    return {
        "message": "Document uploaded and indexed successfully.",
        "conversation_id": conversation.id,
        "filename": filename,
        "chunks": chunks,
    }
