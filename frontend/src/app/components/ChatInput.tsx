"use client";

import { useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { UploadModal } from "./UploadModal";
import type { DocumentItem } from "@/app/types/interfaces";

// ─── Icons ────────────────────────────────────────────────────────────────────

function SendIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
    </svg>
  );
}

function PaperclipIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
    </svg>
  );
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface ChatInputProps {
  onSend?: (message: string) => void;
  onUploadComplete?: (doc: DocumentItem) => void;
  disabled?: boolean;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function ChatInput({
  onSend = () => { },
  onUploadComplete,
  disabled = false,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [showUpload, setShowUpload] = useState(false);

  const handleSubmit = (e: FormEvent | KeyboardEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <div className="relative flex items-center bg-[var(--input-bg)] rounded-2xl border border-[var(--input-border)]">

          {/* Upload button */}
          <button
            type="button"
            onClick={() => setShowUpload(true)}
            disabled={disabled}
            title="Tải lên tài liệu"
            className="ml-2 p-1.5 sm:p-2 rounded-lg
              text-[var(--text-secondary)]
              hover:text-[var(--accent-color)] hover:bg-[var(--accent-color)]/10
              disabled:opacity-30 disabled:cursor-not-allowed
              transition-all"
          >
            <PaperclipIcon />
          </button>

          {/* Textarea */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập tin nhắn..."
            disabled={disabled}
            rows={1}
            className="flex-1 bg-transparent text-[var(--text-primary)]
              px-2 sm:px-3 py-2.5 sm:py-3 resize-none text-sm sm:text-base
              focus:outline-none rounded-2xl
              placeholder:text-[var(--text-secondary)]
              disabled:opacity-50"
          />

          {/* Send button */}
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="mr-2 p-1.5 sm:p-2 rounded-lg
              bg-[var(--accent-color)] text-white
              hover:bg-[var(--accent-color)]/80
              disabled:opacity-30 disabled:cursor-not-allowed
              transition-all"
          >
            <SendIcon />
          </button>
        </div>

        <p className="text-xs sm:text-sm text-[var(--text-secondary)] text-center mt-2">
          Enter để gửi · Shift+Enter để xuống dòng
        </p>
      </form>

      {/* Upload Modal */}
      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUploadComplete={(doc) => {
            setShowUpload(false);
            onUploadComplete?.(doc);
          }}
        />
      )}
    </>
  );
}