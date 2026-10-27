
import { useCallback, useEffect, useState } from "react";
import {
    Clock3,
    MessageSquare,
    Plus,
    Trash2,
    LoaderCircle,
    RefreshCw,
    Search,
    FileText,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function HistorySidebar({
    activeConversationId,
    onSelectConversation,
    onNewConversation,
    refreshKey = 0,
}) {
    const [conversations, setConversations] = useState([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [deletingId, setDeletingId] = useState(null);
    const [error, setError] = useState("");

    const loadHistory = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const response = await fetch(`${API_URL}/api/history`);

            if (!response.ok) {
                throw new Error("Could not load conversation history.");
            }

            const data = await response.json();

            setConversations(data.conversations || []);
        } catch (err) {
            setError(err.message || "Unable to load history.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadHistory();
    }, [loadHistory, refreshKey]);

    async function handleDelete(event, conversationId) {
        event.stopPropagation();

        const confirmed = window.confirm(
            "Delete this conversation and its saved messages?"
        );

        if (!confirmed) return;

        setDeletingId(conversationId);
        setError("");

        try {
            const response = await fetch(
                `${API_URL}/api/history/${conversationId}`,
                { method: "DELETE" }
            );

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || "Could not delete conversation.");
            }

            setConversations((previous) =>
                previous.filter((item) => item.id !== conversationId)
            );

            if (Number(activeConversationId) === Number(conversationId)) {
                onNewConversation?.();
            }
        } catch (err) {
            setError(err.message || "Unable to delete conversation.");
        } finally {
            setDeletingId(null);
        }
    }

    const filteredConversations = conversations.filter((conversation) => {
        const query = search.trim().toLowerCase();

        if (!query) return true;

        return (
            (conversation.title || "").toLowerCase().includes(query) ||
            (conversation.document_filename || "").toLowerCase().includes(query) ||
            (conversation.last_message || "").toLowerCase().includes(query)
        );
    });

    function formatDate(value) {
        if (!value) return "";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) return "";

        const now = new Date();
        const sameDay = date.toDateString() === now.toDateString();

        if (sameDay) {
            return date.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
            });
        }

        return date.toLocaleDateString([], {
            month: "short",
            day: "numeric",
        });
    }

    return (
        <section className="history-section">
            <div className="history-heading">
                <div className="history-title">
                    <Clock3 size={16} />
                    <span>History</span>
                </div>

                <button
                    type="button"
                    className="history-icon-button"
                    onClick={loadHistory}
                    title="Refresh history"
                    aria-label="Refresh history"
                    disabled={loading}
                >
                    {loading ? (
                        <LoaderCircle size={15} className="spin" />
                    ) : (
                        <RefreshCw size={15} />
                    )}
                </button>
            </div>

            <button
                type="button"
                className="history-new-button"
                onClick={() => onNewConversation?.()}
            >
                <Plus size={16} />
                <span>New conversation</span>
            </button>

            <label className="history-search">
                <Search size={15} />

                <input
                    type="search"
                    placeholder="Search conversations..."
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                />
            </label>

            {error && (
                <div className="history-error" role="alert">
                    {error}
                    <button type="button" onClick={loadHistory}>
                        Retry
                    </button>
                </div>
            )}

            <div className="history-list">
                {loading && conversations.length === 0 ? (
                    <div className="history-empty">
                        <LoaderCircle size={19} className="spin" />
                        <span>Loading history...</span>
                    </div>
                ) : filteredConversations.length === 0 ? (
                    <div className="history-empty">
                        <MessageSquare size={21} />
                        <span>
                            {search
                                ? "No matching conversations."
                                : "Your conversations will appear here."}
                        </span>
                    </div>
                ) : (
                    filteredConversations.map((conversation) => {
                        const active =
                            Number(activeConversationId) === Number(conversation.id);

                        return (
                            <button
                                type="button"
                                key={conversation.id}
                                className={`history-item ${active ? "active" : ""}`}
                                onClick={() => onSelectConversation?.(conversation.id)}
                                title={conversation.title}
                            >
                                <MessageSquare
                                    className="history-item-icon"
                                    size={17}
                                />

                                <span className="history-item-content">
                                    <span className="history-item-title">
                                        {conversation.title || "Product inquiry"}
                                    </span>

                                    <span className="history-item-preview">
                                        {conversation.document_filename ? (
                                            <>
                                                <FileText size={12} />
                                                {conversation.document_filename}
                                            </>
                                        ) : (
                                            conversation.last_message || "No messages yet"
                                        )}
                                    </span>

                                    <span className="history-item-meta">
                                        {formatDate(conversation.updated_at)}
                                        {conversation.message_count > 0 &&
                                            ` · ${conversation.message_count} messages`}
                                    </span>
                                </span>

                                <span
                                    className="history-delete-wrap"
                                    onClick={(event) => event.stopPropagation()}
                                >
                                    <button
                                        type="button"
                                        className="history-delete-button"
                                        aria-label={`Delete ${conversation.title}`}
                                        title="Delete conversation"
                                        disabled={deletingId === conversation.id}
                                        onClick={(event) =>
                                            handleDelete(event, conversation.id)
                                        }
                                    >
                                        {deletingId === conversation.id ? (
                                            <LoaderCircle size={14} className="spin" />
                                        ) : (
                                            <Trash2 size={14} />
                                        )}
                                    </button>
                                </span>
                            </button>
                        );
                    })
                )}
            </div>
        </section>
    );
}
