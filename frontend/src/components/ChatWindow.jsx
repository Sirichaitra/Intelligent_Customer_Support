
import Message from "./Message";
import SuggestedQuestions from "./SuggestedQuestions";

const DEFAULT_QUESTIONS = [
    "What is this document about?",
    "Summarize the key points",
    "What are the important details?"
];

export default function ChatWindow({
    messages = [],
    loading = false,
    onSuggestedQuestion,
    onFeedback
}) {
    return (
        <div className="chat-window">
            {messages.length === 0 ? (
                <div className="document-welcome">
                    <div className="ai-orb">
                        <span>✦</span>
                    </div>

                    <h2>How can I help you?</h2>
                    <p>
                        Upload a document and ask questions.
                        I'll find relevant information and answer
                        using the document's content.
                    </p>

                    <SuggestedQuestions
                        questions={DEFAULT_QUESTIONS}
                        onSelect={onSuggestedQuestion}
                    />
                </div>
            ) : (
                <div className="messages-list">
                    {messages.map((message, index) => (
                        <Message
                            key={message.id ?? index}
                            message={message}
                            onFeedback={onFeedback}
                        />
                    ))}
                </div>
            )}

            {loading && (
                <div className="loading-indicator">
                    <span className="loading-dot" />
                    <span className="loading-dot" />
                    <span className="loading-dot" />
                    <span>Searching your document...</span>
                </div>
            )}
        </div>
    );
}
