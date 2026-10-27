
import { Sparkles, ArrowUpRight } from "lucide-react";

export default function SuggestedQuestions({
    questions = [],
    onSelect
}) {
    if (questions.length === 0) {
        return null;
    }

    return (
        <div className="suggestions document-suggestions">
            <div className="suggestions-heading">
                <Sparkles size={16} />
                <span>Try asking</span>
            </div>

            <div className="suggestion-list">
                {questions.map((question, index) => (
                    <button
                        type="button"
                        className="suggestion-item"
                        key={index}
                        onClick={() => onSelect?.(question)}
                    >
                        <span>{question}</span>
                        <ArrowUpRight size={16} />
                    </button>
                ))}
            </div>
        </div>
    );
}
