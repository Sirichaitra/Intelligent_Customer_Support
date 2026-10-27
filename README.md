# SupportIQ – Intelligent Product Support Assistant

SupportIQ is an AI-powered product support application that allows users to upload product documents and ask questions about their contents. It uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from uploaded documents and generate answers using Google's Gemini API.

The application is being developed with a React frontend and a FastAPI backend, with FAISS for vector-based document retrieval and SQLite for conversation history.

## Features

- **Document Upload:** Upload product documents in PDF, TXT, and DOCX formats.
- **Document Processing:** Extract text and split it into smaller chunks for efficient retrieval.
- **Semantic Search:** Generate embeddings using Sentence Transformers and store document vectors in FAISS.
- **AI-Powered Question Answering:** Use Gemini to generate answers based on retrieved document passages.
- **Conversation Management:** Create, retrieve, list, and delete conversations.
- **Conversation History:** Store user questions and AI responses using SQLAlchemy and SQLite.
- **Source Tracking:** Return source document information and page or chunk metadata with answers.
- **Conversation-Specific Indexing:** Maintain a separate FAISS index for each conversation.
- **Unsupported Question Handling:** Inform users when the retrieved document context does not provide enough information to answer a question.

## Tech Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| LLM | Google Gemini API |
| RAG Framework | LangChain |
| Embeddings | Sentence Transformers |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector Database | FAISS |
| Database | SQLite |
| ORM | SQLAlchemy |
| Document Processing | PyPDF, python-docx |
| API Testing | FastAPI Swagger UI |

## System Architecture

```text
                 User
                  |
                  v
          React Frontend
                  |
                  v
           FastAPI Backend
                  |
          +-------+-------+
          |               |
          v               v
   Document Upload    User Questions
          |               |
          v               v
   Text Extraction   FAISS Retrieval
          |               |
          v               v
   Text Chunking     Relevant Passages
          |               |
          v               v
   Embeddings        Gemini API
          |               |
          v               v
      FAISS Index     Generated Answer
                          |
                          v
                  Answer and Sources
                          |
                          v
                  React Frontend

       SQLite stores conversation history
       and associated messages.
```

## Project Structure

```text
SupportIQ/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   ├── routes/
│   │   │   └── history.py
│   │   └── services/
│   │       ├── document_rag.py
│   │       └── rag_services.py
│   ├── data/
│   │   └── vector_stores/
│   ├── .env
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── Message.jsx
│   │   │   └── SuggestedQuestions.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── index.html
│
├── .gitignore
└── README.md
```

*The structure is representative of the current implementation. Adjust filenames and folders to match your actual repository.*

## Prerequisites

Install the following before running the project:

- Python 3.10 or later
- Node.js and npm
- A Google Gemini API key
- Git

## Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SupportIQ
```

Replace the placeholder with your actual GitHub repository URL.

### 2. Set up the backend

Open a terminal and navigate to the backend directory.

```bash
cd backend
```

Create and activate a Python virtual environment.

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

If the requirements file has not yet been created, install the packages used by the current implementation:

```bash
pip install fastapi uvicorn python-multipart python-dotenv
pip install google-genai sqlalchemy
pip install langchain-community langchain-core
pip install langchain-huggingface langchain-text-splitters
pip install sentence-transformers faiss-cpu pypdf python-docx
```

### 3. Configure environment variables

Create a `.env` file inside the `backend` directory.

```env
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Replace the placeholders with your actual API key and a Gemini model identifier supported by your API key.

Keep the API key on the backend. Never expose it in frontend code or commit the `.env` file to GitHub.

### 4. Run the backend

From the `backend` directory, activate the virtual environment and run:

```bash
uvicorn app.main:app --reload
```

The backend should be available at:

- API root: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs

Use Swagger UI to upload a document and test the API endpoints.

### 5. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically:

http://localhost:5173/

Ensure that the frontend sends requests to the correct FastAPI backend URL.

## API Endpoints

### Document and Question APIs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Check backend status |
| POST | `/api/upload` | Upload and process a product document |
| POST | `/api/ask` | Ask a question about an uploaded document |

### Conversation History APIs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/history` | Retrieve conversation history |
| POST | `/api/history` | Create a conversation |
| GET | `/api/history/{conversation_id}` | Retrieve a specific conversation |
| DELETE | `/api/history/{conversation_id}` | Delete a conversation |

## Testing the APIs

### Upload a document

In Swagger UI, expand `POST /api/upload`, select **Try it out**, and upload a supported product document.

The endpoint returns information about the uploaded document and its conversation ID.

### Ask a question

Use the conversation ID returned by the upload endpoint.

Example request for `POST /api/ask`:

```json
{
  "conversation_id": 7,
  "question": "What display specifications are listed in the document?"
}
```

Replace `7` with the actual conversation ID.

The response is expected to contain the generated answer, source metadata, and a boolean indicating whether the answer was supported.

```json
{
  "conversation_id": 7,
  "question": "What display specifications are listed in the document?",
  "answer": "Answer generated from the uploaded document.",
  "sources": [
    {
      "source": "product_manual.pdf",
      "page": 3,
      "chunk": 5
    }
  ],
  "supported": true
}
```

*The example response is illustrative; actual answers and source metadata depend on the uploaded document.*

## How the RAG Pipeline Works

1. The user uploads a product document.
2. The backend extracts readable text from the document.
3. The text is divided into overlapping chunks.
4. Sentence Transformers generates embeddings for the chunks.
5. FAISS stores the embeddings in a conversation-specific vector index.
6. When a question is submitted, FAISS retrieves the most relevant passages.
7. The retrieved passages and question are sent to Gemini.
8. Gemini generates an answer constrained by the retrieved document context.
9. The answer and source metadata are returned and saved in the conversation history.

## Security and Configuration

- Store API keys in backend environment variables.
- Exclude `.env`, virtual environments, generated databases, and other local secrets from version control.
- Load only trusted, application-generated FAISS index files when using FAISS deserialization.
- Validate uploaded file types and handle malformed documents.
- Configure CORS to allow only the required frontend origins in production.

## Current Development Status

**Implemented or integrated so far:**

- FastAPI application and Swagger documentation.
- PDF, TXT, and DOCX text extraction.
- Text chunking and Sentence Transformers embeddings.
- Conversation-specific FAISS indexing and retrieval.
- Gemini API integration for answer generation.
- Conversation history endpoints and database persistence.
- Source metadata in RAG responses.

**Work in progress:**

- Improving retrieval relevance for broad and specific questions.
- Verifying that Gemini consistently generates answers from the retrieved passages.
- Testing unsupported-question handling.
- Validating end-to-end integration between the React frontend and FastAPI backend.

The project is under active development, and end-to-end answer quality still needs validation across different product documents.

## Future Enhancements

- Improve retrieval using hybrid search and reranking.
- Support larger document collections and multiple document formats.
- Add document previews and clickable source references.
- Improve answer evaluation and retrieval-quality metrics.
- Add automated tests for document ingestion, retrieval, and answer generation.
- Add production deployment, authentication, and monitoring.

## License

A license has not yet been specified. Add an appropriate license before distributing the project publicly.
