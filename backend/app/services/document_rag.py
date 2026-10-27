
import re
import shutil
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document as WordDocument


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
VECTOR_DIR = BACKEND_DIR / "data" / "vector_stores"

load_dotenv(ENV_FILE)
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings = None


# --------------------------------------------------
# Embeddings
# --------------------------------------------------

def get_embeddings():
    """Load the embedding model once and reuse it."""
    global _embeddings

    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embeddings


# --------------------------------------------------
# Document extraction
# --------------------------------------------------

def extract_documents(filename: str, content: bytes) -> list[Document]:
    """Extract text while preserving page metadata where possible."""

    extension = Path(filename).suffix.lower()
    documents = []

    if extension == ".pdf":
        reader = PdfReader(BytesIO(content))

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": filename,
                            "page": page_number,
                        },
                    )
                )

    elif extension == ".txt":
        text = content.decode("utf-8-sig", errors="replace")

        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": filename, "page": None},
                )
            )

    elif extension == ".docx":
        word_doc = WordDocument(BytesIO(content))

        parts = [
            paragraph.text.strip()
            for paragraph in word_doc.paragraphs
            if paragraph.text.strip()
        ]

        for table in word_doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells
                )

                if row_text.strip():
                    parts.append(row_text)

        text = "\n".join(parts)

        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": filename, "page": None},
                )
            )

    else:
        raise ValueError(
            "Unsupported file type. Upload a PDF, TXT, or DOCX file."
        )

    if not documents:
        raise ValueError(
            "No readable text was found. Scanned PDFs may require OCR."
        )

    return documents


# --------------------------------------------------
# Conversation-specific FAISS paths
# --------------------------------------------------

def get_vector_path(conversation_id: str | int) -> Path:
    """Return the FAISS index path for one conversation."""

    conversation_id = str(conversation_id).strip()

    if not conversation_id or not conversation_id.isdigit():
        raise ValueError("A valid numeric conversation ID is required.")

    return VECTOR_DIR / f"conversation_{conversation_id}"


# --------------------------------------------------
# Create and save index
# --------------------------------------------------

def process_document(
    filename: str,
    content: bytes,
    conversation_id: str | int,
) -> dict:
    """Extract, split, embed, and persist a document."""

    if not content:
        raise ValueError("The uploaded file is empty.")

    conversation_id = str(conversation_id)
    documents = extract_documents(filename, content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = [
        chunk
        for chunk in splitter.split_documents(documents)
        if chunk.page_content.strip()
    ]

    if not chunks:
        raise ValueError("No usable text chunks were created.")

    for index, chunk in enumerate(chunks, start=1):
        chunk.metadata["source"] = filename
        chunk.metadata["chunk"] = index
        chunk.metadata["conversation_id"] = conversation_id

    print(f"[RAG] Creating embeddings for {len(chunks)} chunks...")

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
    )

    vector_path = get_vector_path(conversation_id)
    vector_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = vector_path.with_name(
        vector_path.name + "_temporary"
    )

    if temporary_path.exists():
        shutil.rmtree(temporary_path)

    vector_store.save_local(str(temporary_path))

    if vector_path.exists():
        shutil.rmtree(vector_path)

    temporary_path.rename(vector_path)

    print(f"[RAG] Saved index: {vector_path}")

    return {
        "message": "Document processed successfully.",
        "conversation_id": int(conversation_id),
        "filename": filename,
        "chunks": len(chunks),
    }


# --------------------------------------------------
# Load an index
# --------------------------------------------------

def load_vector_store(conversation_id: str | int) -> FAISS:
    """Load only the index associated with this conversation."""

    vector_path = get_vector_path(conversation_id)
    faiss_file = vector_path / "index.faiss"
    metadata_file = vector_path / "index.pkl"

    if not faiss_file.is_file() or not metadata_file.is_file():
        raise FileNotFoundError(
            f"No FAISS index exists for conversation {conversation_id}. "
            "Upload the document again for this conversation."
        )

    return FAISS.load_local(
        str(vector_path),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


# --------------------------------------------------
# Query expansion
# --------------------------------------------------

def build_query_variants(question: str) -> list[str]:
    """
    Create a small set of related search queries.

    The original question is always searched. Additional queries help
    retrieve relevant passages when the wording differs from the document.
    """

    question = question.strip()
    normalized = question.lower()
    variants = [question]

    def add_variant(query: str):
        query = query.strip()

        if query and query.lower() not in {
            item.lower() for item in variants
        }:
            variants.append(query)

    # Charging and battery-related questions
    charging_terms = (
        "charging",
        "charger",
        "charging capacity",
        "charging speed",
        "charging time",
        "battery",
        "power adapter",
    )

    if any(term in normalized for term in charging_terms):
        add_variant(f"Charging specifications: {question}")
        add_variant("Battery capacity and battery specifications")
        add_variant("Charging speed, charging power, and charging time")

    # Display-related questions
    if any(
        term in normalized
        for term in ("display", "screen", "resolution", "brightness")
    ):
        add_variant(f"Display and screen specifications: {question}")

    # Camera-related questions
    if any(
        term in normalized
        for term in ("camera", "photography", "selfie", "video recording")
    ):
        add_variant(f"Camera specifications and features: {question}")

    # General product specification questions
    if any(
        term in normalized
        for term in ("specification", "specifications", "features", "capacity")
    ):
        add_variant(f"Product technical specifications: {question}")

    return variants[:4]


# --------------------------------------------------
# Retrieve passages
# --------------------------------------------------

def retrieve_chunks(
    question: str,
    conversation_id: str | int,
    k: int = 4,
) -> list[dict]:
    """
    Retrieve document passages using multiple query formulations.

    Results are deduplicated by chunk and ranked by their best FAISS
    distance. FAISS L2 distance is lower for closer vectors.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    vector_store = load_vector_store(conversation_id)

    # Search more candidates than the final number of passages.
    candidate_k = max(k, 8)
    query_variants = build_query_variants(question)

    # Keep the best distance found for each unique document chunk.
    best_results = {}

    for query in query_variants:
        try:
            results = vector_store.similarity_search_with_score(
                query,
                k=candidate_k,
            )
        except Exception as exc:
            print(f"[RAG] Search failed for query {query!r}: {exc}")
            continue

        for document, distance in results:
            text = document.page_content.strip()

            if not text:
                continue

            metadata = document.metadata or {}

            # Chunk numbers are assigned during ingestion.
            # Include source and page to prevent accidental collisions.
            key = (
                metadata.get("source", "Uploaded document"),
                metadata.get("page"),
                metadata.get("chunk"),
            )

            distance = float(distance)

            candidate = {
                "text": text,
                "source": metadata.get("source", "Uploaded document"),
                "page": metadata.get("page"),
                "chunk": metadata.get("chunk"),
                "distance": distance,
            }

            previous = best_results.get(key)

            if previous is None or distance < previous["distance"]:
                best_results[key] = candidate

    # Lower FAISS L2 distance ranks first.
    passages = sorted(
        best_results.values(),
        key=lambda item: item["distance"],
    )

    # Return up to eight passages to provide the LLM with more context.
    final_k = max(k, 8)
    passages = passages[:final_k]

    print(
        f"[RAG] Conversation {conversation_id}: "
        f"{len(passages)} unique passages retrieved "
        f"from {len(query_variants)} query formulation(s)."
    )

    for index, passage in enumerate(passages, start=1):
        print(
            f"[RAG] Result {index}: "
            f"distance={passage['distance']:.4f}, "
            f"source={passage['source']}, "
            f"page={passage['page']}, "
            f"chunk={passage['chunk']}"
        )

    return passages
