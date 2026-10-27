from fastapi import UploadFile, File, HTTPException
from pydantic import BaseModel

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models
from app.routes import chat, documents, history

app = FastAPI(title="SupportIQ Product Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(history.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"message": "SupportIQ API is running"}

from app.services.document_rag import (
    process_document,
)


class QuestionRequest(BaseModel):
    question: str


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(400, "Filename is required.")

        content = await file.read()

        result = process_document(file.filename, content)
        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    finally:
        await file.close()


@app.post("/api/ask")
async def ask_question(request: QuestionRequest):
    try:
        return answer_question(request.question)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        # Avoid exposing API keys or internal exception details.
        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer. Check the backend logs.",
        )