
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, UserRound, ThumbsUp, ThumbsDown, FileText } from "lucide-react";

export default function Message({ message, onFeedback }) {
    const isUser = message.role === "user";

    const sources = Array.isArray(message.sources)
        ? message.sources
        : [];

    return (
        <div className={`message-row ${isUser ? "user-message" : "assistant-message"}`}>
            <div className="message-avatar">
                {isUser ? <UserRound size={19} /> : <Bot size={19} />}
            </div>

            <div className="message-content-wrapper">
                <div className="message-sender">
                    {isUser ? "You" : "SupportIQ"}
                </div>

                <div className="message-bubble">
                    {isUser ? (
                        <div className="message-text">
                            {message.content}
                        </div>
                    ) : (
                        <div className="markdown-content">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    a: ({ children, href }) => (
                                        <a
                                            href={href}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            {children}
                                        </a>
                                    ),
                                }}
                            >
                                {message.content || ""}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>

                {!isUser && sources.length > 0 && (
                    <div className="message-sources">
                        <div className="sources-heading">
                            <FileText size={16} />
                            <span>Sources from your document</span>
                        </div>

                        {sources.map((source, index) => (
                            <div
                                className="source-item"
                                key={`${source.source}-${source.page}-${source.chunk}-${index}`}
                            >
                                <div className="source-name">
                                    {source.source || "Uploaded document"}
                                </div>

                                {source.page != null && (
                                    <span className="source-page">
                                        Page {source.page}
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {!isUser && (
                    <div className="message-feedback">
                        <button
                            type="button"
                            className={`feedback-button ${message.feedback === "up" ? "selected positive" : ""}`}
                            onClick={() => onFeedback?.(message.id, "up")}
                            aria-label="Good response"
                            aria-pressed={message.feedback === "up"}
                            title="Good response"
                        >
                            <ThumbsUp size={17} strokeWidth={1.8} />
                        </button>

                        <button
                            type="button"
                            className={`feedback-button ${message.feedback === "down" ? "selected negative" : ""}`}
                            onClick={() => onFeedback?.(message.id, "down")}
                            aria-label="Bad response"
                            aria-pressed={message.feedback === "down"}
                            title="Bad response"
                        >
                            <ThumbsDown size={17} strokeWidth={1.8} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
