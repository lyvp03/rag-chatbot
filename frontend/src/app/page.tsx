'use client';

import { useEffect, useRef } from 'react';
import NavBar from './components/NavBar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { TypingIndicator } from './components/TypingIndicator';
import { useChat } from './hooks/useChat';
import type { DocumentItem } from './types/interfaces';

export default function ChatPage() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    stopStreaming,
    clearMessages,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleUploadComplete = (doc: DocumentItem) => {
    console.log('✅ Tài liệu đã được index:', doc.filename);
  };

  const isWaitingFirstToken = isLoading && messages[messages.length - 1]?.content === '';

  return (
    <div className="chat-page flex flex-col h-screen bg-[var(--bg-primary)]">
      <NavBar />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Sub header */}
        <div className="border-b border-[var(--border-color)]">
          <div className="max-w-3xl mx-auto px-3 sm:px-4 py-3 sm:py-4 flex items-center justify-between">
            <h1 className="text-lg sm:text-xl font-semibold text-[var(--text-primary)]">
              Chat với AI Crypto
            </h1>
            <div className="flex items-center gap-3">

              {/* Nút dừng — hiện bất cứ khi nào đang loading */}
              {isLoading && (
                <button
                  onClick={stopStreaming}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
                    text-red-400 border border-red-400/40
                    hover:bg-red-400/10 transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="6" y="6" width="12" height="12" rx="2" />
                  </svg>
                  Dừng
                </button>
              )}

              {messages.length > 0 && !isLoading && (
                <button
                  onClick={clearMessages}
                  className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                >
                  Xóa lịch sử
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-3xl mx-auto px-3 sm:px-4 py-4 sm:py-6">

            {messages.length === 0 && !isLoading && (
              <div className="text-center text-[var(--text-secondary)] py-12 sm:py-20">
                <p className="text-lg sm:text-xl mb-2 sm:mb-3"> </p>
                <p className="text-sm sm:text-base"> </p>
              </div>
            )}

            {messages.map((msg, index) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                isLatest={index === messages.length - 1}
                enableTyping={
                  msg.role === 'assistant' &&
                  msg.isStreaming === false &&
                  index === messages.length - 1
                }
              />
            ))}

            {/* Typing indicator chỉ khi chờ token đầu tiên */}
            {isWaitingFirstToken && <TypingIndicator />}

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-3 sm:px-4 py-2 sm:py-3 rounded-lg mb-4 animate-fade-in text-sm sm:text-base">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="bg-[var(--bg-primary)]/80 backdrop-blur-sm border-t border-[var(--border-color)] p-3 sm:p-4">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSend={sendMessage}
              onUploadComplete={handleUploadComplete}
              disabled={isLoading}
            />
          </div>
        </div>

      </main>
    </div>
  );
}