import React, { useState } from "react";
import { Send, Loader2 } from "lucide-react";
import { cn } from "../../../lib/utils";
import axios from "axios";
import chatBg from "../../../assets/chat_bg.png";

const ChatMessage = ({ message, isUser }) => {
  return (
    <div
      className={cn(
        "flex w-full mb-2",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "rounded-lg px-4 py-2 max-w-[80%]",
          isUser
            ? "bg-indigo-600/30 text-white rounded-tr-none backdrop-blur-sm shadow-md border border-indigo-400/30"
            : message.error
            ? "bg-red-800/30 text-gray-100 rounded-tl-none backdrop-blur-sm shadow-md border border-red-400/30"
            : "bg-gray-800/20 text-gray-100 rounded-tl-none backdrop-blur-sm shadow-md border border-gray-400/20"
        )}
      >
        <p>{message.text}</p>
      </div>
    </div>
  );
};

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I am Empyrean, your guide to the world of books. How can I help you today?",
      isUser: false,
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // API endpoint
  const API_URL = "https://scribesofempyrean.onrender.com/api/chat";

  const handleSendMessage = async () => {
    if (inputValue.trim() === "") return;

    // Add user message
    const newUserMessage = {
      id: messages.length + 1,
      text: inputValue,
      isUser: true,
    };

    setMessages([...messages, newUserMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      // Call the API
      const response = await axios.post(API_URL, {
        query: inputValue,
        session_id: sessionId,
      });

      // Store the session ID for future requests
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      // Add AI response
      const aiResponse = {
        id: messages.length + 2,
        text: response.data.answer,
        isUser: false,
        context: response.data.context_used,
      };

      setMessages((prev) => [...prev, aiResponse]);
    } catch (err) {
      console.error("Error fetching response:", err);
      setError("Failed to get a response. Please try again.");

      // Add error message as AI response
      const errorResponse = {
        id: messages.length + 2,
        text: "I'm sorry, I encountered an error. Please try again later.",
        isUser: false,
        error: true,
      };

      setMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div
      style={{
        backgroundImage: `url(${chatBg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
      }}
    >
      <div className="flex flex-col h-screen w-full max-w-6xl mx-auto px-2 py-2 z-10">
        <div className="flex items-center mb-2">
          <h1 className="text-3xl font-bold text-white">Empyrean Chat</h1>
        </div>

        {/* Messages container */}
        <div className="flex-1 overflow-y-auto mb-2 pr-2 custom-scrollbar">
          <div className="space-y-2 py-2">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                isUser={message.isUser}
              />
            ))}
          </div>
        </div>

        {/* Input area */}
        <div className="relative bg-white rounded-lg border mb-1">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about books, authors, or literary worlds..."
            className="w-full text-gray-900 p-3 pr-12 outline-none resize-none h-[50px] rounded-lg placeholder:text-gray-500 bg-transparent"
            rows="1"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={inputValue.trim() === "" || isLoading}
            className="absolute right-3 bottom-3 p-2 rounded-full bg-indigo-600/70 hover:bg-indigo-700/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 text-white animate-spin" />
            ) : (
              <Send className="h-5 w-5 text-white" />
            )}
          </button>
        </div>

        {/* Error message */}
        {error && <div className="mt-2 text-red-400 text-sm">{error}</div>}
      </div>
    </div>
  );
}
