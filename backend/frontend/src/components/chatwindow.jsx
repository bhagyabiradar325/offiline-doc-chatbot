import { useState } from "react";
import Message from "./message.jsx";

export default function ChatWindow({ messages, onAsk, onOpenPage }) {
  const [question, setQuestion] = useState("");
  const isThinking = messages.some((message) => message.loading);

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || isThinking) return;

    setQuestion("");
    await onAsk(cleanQuestion);
  }

  return (
    <section className="chat-panel">
      <div className="chat-header">
        <h2>Ask your PDF</h2>
      </div>

      <div className="message-list">
        {messages.map((message, index) => (
          <Message key={index} message={message} onOpenPage={onOpenPage} />
        ))}
      </div>

      <form className="question-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Example: Which table shows revenue?"
          required
        />
        <button type="submit" disabled={isThinking}>
          Ask
        </button>
      </form>
    </section>
  );
}
