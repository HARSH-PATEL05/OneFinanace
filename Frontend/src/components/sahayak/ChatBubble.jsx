import { useState, useRef, useEffect } from "react";
import { sendMessage, clearChat } from "./api";
import styles from "./ChatBubble.module.css";

export default function ChatBubble() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm Sahayak, your personal finance assistant. Ask me anything about budgeting, investing, or Indian markets 📈" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput("");
    setIsLoading(true);

    setMessages(prev => [...prev, { role: "user", content: text }]);
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    await sendMessage(
      text,
      sessionId,
      (token) => {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: updated[updated.length - 1].content + token,
          };
          return updated;
        });
      },
      (newSessionId) => {
        setSessionId(newSessionId);
        setIsLoading(false);
      }
    );
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  async function handleClear() {
    if (sessionId) await clearChat(sessionId);
    setSessionId(null);
    setMessages([
      { role: "assistant", content: "Chat cleared! Ask me anything 😊" }
    ]);
  }

  return (
    <div className={styles["sahayak-wrapper"]}>
      {isOpen && (
        <div className={styles["sahayak-window"]}>
          
          {/* Header */}
          <div className={styles["sahayak-header"]}>
            <div className={styles["sahayak-header-info"]}>
              <div className={styles["sahayak-avatar"]}>S</div>
              <div>
                <div className={styles["sahayak-name"]}>Sahayak</div>
                <div className={styles["sahayak-status"]}>
                  {isLoading ? "typing..." : "Finance Assistant"}
                </div>
              </div>
            </div>

            <div className={styles["sahayak-header-actions"]}>
              <button
                onClick={handleClear}
                className={styles["sahayak-clear-btn"]}
                title="Clear chat"
              >
                ↺
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className={styles["sahayak-close-btn"]}
                title="Close"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className={styles["sahayak-messages"]}>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`${styles["sahayak-msg"]} ${
                  styles[`sahayak-msg--${msg.role}`]
                }`}
              >
                <div className={styles["sahayak-bubble"]}>
                  {msg.content}
                </div>
              </div>
            ))}

            {isLoading && messages[messages.length - 1]?.content === "" && (
              <div className={styles["sahayak-typing"]}>
                <span /><span /><span />
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className={styles["sahayak-input-row"]}>
            <textarea
              ref={inputRef}
              className={styles["sahayak-input"]}
              placeholder="Ask about finance..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={isLoading}
            />
            <button
              className={styles["sahayak-send-btn"]}
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
            >
              ➤
            </button>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        className={`${styles["sahayak-fab"]} ${
          isOpen ? styles["sahayak-fab--open"] : ""
        }`}
        onClick={() => setIsOpen(prev => !prev)}
        title="Chat with Sahayak"
      >
        {isOpen ? "✕" : "💬"}
      </button>
    </div>
  );
}