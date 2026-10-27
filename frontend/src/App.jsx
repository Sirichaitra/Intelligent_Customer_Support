
import { useRef, useState } from "react";

import {
  Bot,
  Plus,
  Send,
  ShieldCheck,
  Sparkles,
  PanelLeftClose,
  MessageSquare,
  RotateCcw,
  FileUp,
  FileText,
  CheckCircle2,
  X,
  LoaderCircle,
} from "lucide-react";

import ChatWindow from "./components/ChatWindow.jsx";
import "./index.css";

// FastAPI backend
const API_URL = "http://127.0.0.1:8000";

function getErrorMessage(data, fallback) {
  const detail = data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (detail != null) {
    return JSON.stringify(detail);
  }

  if (typeof data?.message === "string") {
    return data.message;
  }

  return fallback;
}

function getAnswerText(answer) {
  if (typeof answer === "string") {
    return answer;
  }

  if (answer != null) {
    return JSON.stringify(answer);
  }

  return "No data found in the uploaded document.";
}

export default function App() {
  const fileInputRef = useRef(null);

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [documentInfo, setDocumentInfo] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState("");

  const documentReady =
    Boolean(documentInfo) && conversationId != null;

  function createId() {
    return `${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 8)}`;
  }

  function startNewChat() {
    setMessages([]);
    setQuestion("");
    setError("");
  }

  function handleFileSelection(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    const allowedExtensions = [".pdf", ".txt", ".docx"];

    const extension = file.name
      .slice(file.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setError("Please select a PDF, TXT, or DOCX document.");
      event.target.value = "";
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("The maximum document size is 10 MB.");
      event.target.value = "";
      return;
    }

    setError("");
    setSelectedFile(file);
  }

  async function uploadDocument() {
    if (!selectedFile || uploading) return;

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();

      formData.append("file", selectedFile);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            `Document upload failed (${response.status}).`
          )
        );
      }

      // The backend must return the ID used by /api/ask.
      const newConversationId = data.conversation_id;

      if (
        newConversationId === undefined ||
        newConversationId === null
      ) {
        throw new Error(
          "The upload API did not return conversation_id. " +
          "Check the response of POST /api/upload."
        );
      }

      setConversationId(newConversationId);

      setDocumentInfo({
        filename:
          data.filename ||
          data.file_name ||
          selectedFile.name,

        chunks: data.chunks ?? data.chunk_count ?? null,

        message:
          data.message || "Document indexed successfully.",
      });

      setMessages([]);
      setQuestion("");
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : String(err)
      );
    } finally {
      setUploading(false);
    }
  }

  async function askQuestion(text = question) {
    const trimmedQuestion = text.trim();

    if (!trimmedQuestion || loading) return;

    if (!documentReady) {
      setError(
        "Upload and index a document before asking questions."
      );
      return;
    }

    setError("");
    setQuestion("");
    setLoading(true);

    const userMessage = {
      id: createId(),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          question: trimmedQuestion,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            `Unable to answer your question (${response.status}).`
          )
        );
      }

      const answer = getAnswerText(
        data.answer ?? data.response
      );

      const assistantMessage = {
        id: createId(),
        role: "assistant",
        content: answer,
        sources: Array.isArray(data.sources)
          ? data.sources
          : [],
        supported: data.supported ?? true,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : String(err);

      setMessages((previous) => [
        ...previous,
        {
          id: createId(),
          role: "assistant",
          content:
            `Sorry, I couldn't process that question. ${message}`,
          sources: [],
          supported: false,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleFeedback(messageId, rating) {
    setMessages((previous) =>
      previous.map((message) =>
        message.id === messageId
          ? { ...message, feedback: rating }
          : message
      )
    );
  }

  function handleComposerSubmit(event) {
    event.preventDefault();
    askQuestion();
  }

  function handleSuggestedQuestion(text) {
    askQuestion(text);
  }

  return (
    <div className="app-shell">
      {/* Sidebar */}
      {sidebarOpen && (
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="brand">
              <div className="brand-icon">
                <Bot size={23} />
              </div>

              <div className="brand-text">
                <span>SupportIQ</span>
                <small>Intelligent Support</small>
              </div>
            </div>

            <button
              type="button"
              className="icon-button sidebar-close"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              <PanelLeftClose size={19} />
            </button>
          </div>

          <button
            type="button"
            className="new-chat-button"
            onClick={startNewChat}
          >
            <Plus size={18} />
            <span>New conversation</span>
          </button>

          <div className="sidebar-section-label">
            WORKSPACE
          </div>

          <div className="sidebar-nav-item active">
            <MessageSquare size={18} />
            <span>Document assistant</span>
          </div>

          {/* Document upload */}
          <div className="sidebar-card document-sidebar-card">
            <div className="sidebar-card-heading">
              <FileUp size={18} />
              <span>Knowledge source</span>
            </div>

            <p className="sidebar-card-description">
              Upload a document to let SupportIQ answer
              questions from its contents.
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.docx"
              hidden
              onChange={handleFileSelection}
            />

            {!selectedFile ? (
              <button
                type="button"
                className="document-dropzone"
                onClick={() => fileInputRef.current?.click()}
              >
                <FileUp size={23} />
                <span>Choose a document</span>
                <small>PDF, TXT, DOCX · Max 10 MB</small>
              </button>
            ) : (
              <div className="selected-document">
                <FileText size={21} />

                <div className="selected-document-details">
                  <strong>{selectedFile.name}</strong>
                  <small>
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </small>
                </div>

                <button
                  type="button"
                  className="icon-button"
                  onClick={() => {
                    setSelectedFile(null);

                    if (fileInputRef.current) {
                      fileInputRef.current.value = "";
                    }
                  }}
                  aria-label="Remove selected file"
                >
                  <X size={16} />
                </button>
              </div>
            )}

            {selectedFile && (
              <button
                type="button"
                className="index-document-button"
                onClick={uploadDocument}
                disabled={uploading}
              >
                {uploading ? (
                  <>
                    <LoaderCircle size={16} className="spin" />
                    Processing document...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Upload and index
                  </>
                )}
              </button>
            )}

            {documentInfo && (
              <div className="indexed-document">
                <CheckCircle2 size={17} />

                <div>
                  <strong>Document ready</strong>
                  <p>{documentInfo.filename}</p>

                  {documentInfo.chunks != null && (
                    <small>
                      {documentInfo.chunks} text chunks indexed
                    </small>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="sidebar-spacer" />

          <div className="sidebar-footer">
            <div className="security-icon">
              <ShieldCheck size={19} />
            </div>

            <div>
              <strong>Document-grounded AI</strong>
              <p>Answers based on retrieved content</p>
            </div>
          </div>
        </aside>
      )}

      {/* Main workspace */}
      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            {!sidebarOpen && (
              <button
                type="button"
                className="icon-button"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open sidebar"
              >
                <PanelLeftClose size={19} />
              </button>
            )}

            <div className="topbar-title">
              <span>SupportIQ</span>
              <span className="topbar-divider">/</span>
              <span className="topbar-current">
                Document assistant
              </span>
            </div>
          </div>

          <div className="topbar-right">
            <span className="availability-pill">
              <span className="status-dot" />
              {documentReady
                ? "Document ready"
                : "Awaiting document"}
            </span>

            <button
              type="button"
              className="icon-button"
              onClick={startNewChat}
              title="Clear conversation"
              aria-label="Clear conversation"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        </header>

        <section className="chat-area">
          <div className="chat-heading">
            <div className="chat-heading-icon">
              <Sparkles size={21} />
            </div>

            <div>
              <h1>Your AI document assistant</h1>

              <p>
                {documentReady
                  ? `Ask anything about ${documentInfo.filename}`
                  : "Upload a document to get started"}
              </p>
            </div>
          </div>

          {error && (
            <div className="error-toast" role="alert">
              <span>{error}</span>

              <button
                type="button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                <X size={16} />
              </button>
            </div>
          )}

          <ChatWindow
            messages={messages}
            loading={loading}
            onSuggestedQuestion={handleSuggestedQuestion}
            onFeedback={handleFeedback}
          />

          {/* Message composer */}
          <div className="composer-container">
            {!documentReady && (
              <p className="composer-hint">
                <FileText size={15} />
                Upload and index a document before asking a question.
              </p>
            )}

            <form
              className="composer"
              onSubmit={handleComposerSubmit}
            >
              <textarea
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                placeholder={
                  documentReady
                    ? "Ask a question about your document..."
                    : "Upload a document to begin..."
                }
                rows={1}
                disabled={!documentReady || loading}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey &&
                    !event.nativeEvent.isComposing
                  ) {
                    event.preventDefault();

                    if (question.trim() && !loading) {
                      askQuestion();
                    }
                  }
                }}
              />

              <button
                type="submit"
                className="send-button"
                disabled={
                  !documentReady ||
                  !question.trim() ||
                  loading
                }
                aria-label="Send question"
              >
                {loading ? (
                  <LoaderCircle size={19} className="spin" />
                ) : (
                  <Send size={19} />
                )}
              </button>
            </form>

            <p className="composer-disclaimer">
              SupportIQ can make mistakes. Verify important
              details against the original document.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
