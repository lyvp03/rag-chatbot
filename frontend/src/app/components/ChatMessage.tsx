"use client";

import { useEffect, useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useTypingEffect } from '../hooks/useTypingEffect';
import type { Message } from '../hooks/useChat';
import type { SourceChunk } from '../types/interfaces';

interface ChatMessageProps {
    message: Message;
    isLatest?: boolean;
    enableTyping?: boolean;
    onTypingComplete?: () => void;
}

function formatMessage(content: string): string {
    let formatted = content;
    formatted = formatted.replace(/\s{2,}(\d{1,2}[\)\.]\s+[A-Za-zÀ-ỹ])/g, '\n\n$1');
    formatted = formatted.replace(/\s{2,}(-\s+[A-Za-zÀ-ỹ])/g, '\n  $1');
    formatted = formatted.replace(/^(\d{1,2})\)/gm, '$1.');
    formatted = formatted.replace(/\n(\d{1,2})\)/g, '\n$1.');
    return formatted.trim();
}

function formatScore(score: number) {
    return `${Math.round(score * 100)}%`;
}

function fileTypeLabel(type: string) {
    const map: Record<string, string> = {
        pdf: 'PDF', txt: 'TXT', md: 'MD',
        mp3: 'MP3', wav: 'WAV', m4a: 'M4A', webm: 'WEBM',
    };
    return map[type.toLowerCase()] ?? type.toUpperCase();
}

function cleanFilename(filename: string) {
    return filename.replace(/^[a-f0-9-]+_/, '');
}

// ─── Source Chip với popup ────────────────────────────────────────────────────

function SourceChip({ src, index }: { src: SourceChunk; index: number }) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    return (
        <div ref={ref} className="relative">
            <button
                onClick={() => setOpen(v => !v)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs transition-all
                    border cursor-pointer select-none
                    ${open
                        ? 'bg-[var(--accent-color)]/15 border-[var(--accent-color)]/50 text-[var(--accent-color)]'
                        : 'bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-secondary)] hover:border-[var(--accent-color)]/40 hover:text-[var(--text-primary)]'
                    }`}
            >
                <span className={`shrink-0 w-3.5 h-3.5 rounded-full flex items-center justify-center text-[10px] font-bold
                    ${open ? 'bg-[var(--accent-color)] text-white' : 'bg-[var(--input-border)] text-[var(--text-secondary)]'}`}>
                    {index + 1}
                </span>
                <span className="shrink-0 font-medium text-[var(--accent-color)]">
                    {fileTypeLabel(src.file_type)}
                </span>
                <span className="truncate max-w-[100px]">{cleanFilename(src.filename)}</span>
                <span className="shrink-0 opacity-60">·{formatScore(src.relevance_score)}</span>
            </button>

            {open && (
                <div className="absolute bottom-full left-0 mb-2 z-50 w-72
                    bg-[var(--bg-secondary)] border border-[var(--input-border)]
                    rounded-xl shadow-xl overflow-hidden">

                    {/* Header */}
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-[var(--input-border)] bg-[var(--input-bg)]">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[var(--accent-color)]/20 text-[var(--accent-color)]">
                            {fileTypeLabel(src.file_type)}
                        </span>
                        <span className="text-xs font-medium text-[var(--text-primary)] truncate flex-1">
                            {cleanFilename(src.filename)}
                        </span>
                        <span className="text-xs text-[var(--text-secondary)] shrink-0">
                            chunk #{src.chunk_index}
                        </span>
                    </div>

                    {/* Relevance bar */}
                    <div className="px-3 pt-2 pb-1 flex items-center gap-2">
                        <span className="text-[10px] text-[var(--text-secondary)]">Độ liên quan</span>
                        <div className="flex-1 h-1 rounded-full bg-[var(--input-border)] overflow-hidden">
                            <div
                                className="h-full rounded-full bg-[var(--accent-color)]"
                                style={{ width: `${Math.round(src.relevance_score * 100)}%` }}
                            />
                        </div>
                        <span className="text-[10px] font-medium text-[var(--accent-color)]">
                            {formatScore(src.relevance_score)}
                        </span>
                    </div>

                    {/* Preview */}
                    <div className="px-3 pb-3">
                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-5 whitespace-pre-wrap">
                            {src.content_preview}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── Source List ──────────────────────────────────────────────────────────────

function SourceList({ sources }: { sources: Message['sources'] }) {
    if (!sources?.length) return null;

    return (
        <div className="mt-2.5 pt-2.5 border-t border-[var(--border-color)]/40">
            <p className="text-[10px] text-[var(--text-secondary)] mb-1.5 uppercase tracking-wide">
                {sources.length} nguồn tham khảo
            </p>
            <div className="flex flex-wrap gap-1.5">
                {sources.map((src, i) => (
                    <SourceChip key={i} src={src} index={i} />
                ))}
            </div>
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function ChatMessage({
    message,
    isLatest = false,
    enableTyping = false,
    onTypingComplete,
}: ChatMessageProps) {
    const isUser = message.role === 'user';
    const isStreaming = message.isStreaming === true;
    const shouldType = !isUser && isLatest && enableTyping && !isStreaming;

    const { displayedText, isTyping, isComplete } = useTypingEffect({
        text: message.content,
        enabled: shouldType,
    });

    useEffect(() => {
        if (isComplete && shouldType && onTypingComplete) {
            onTypingComplete();
        }
    }, [isComplete, shouldType, onTypingComplete]);

    const rawContent = shouldType ? displayedText : message.content;
    const showCursor = isStreaming || isTyping;
    const contentWithCursor = showCursor ? rawContent + '▋' : rawContent;

    return (
        <div className={`flex mb-3 sm:mb-4 animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[90%] sm:max-w-[80%] px-3 sm:px-4 py-2.5 sm:py-3 rounded-2xl leading-relaxed
                    ${isUser
                        ? 'bg-[var(--user-bubble)] text-[var(--text-primary)] rounded-br-sm'
                        : 'text-[var(--text-primary)] rounded-bl-sm'
                    }`}
                style={!isUser ? { backgroundColor: 'var(--bot-bubble)' } : undefined}
            >
                {isUser ? (
                    <p className="whitespace-pre-wrap text-sm sm:text-base leading-relaxed">
                        {message.content}
                    </p>
                ) : (
                    <>
                        <div className={`prose prose-sm max-w-none text-[var(--text-primary)]
                            prose-strong:text-[var(--text-primary)] prose-strong:font-semibold
                            ${showCursor ? 'typing-cursor' : ''}`}
                        >
                            <ReactMarkdown>{formatMessage(contentWithCursor)}</ReactMarkdown>
                        </div>
                        {!isStreaming && <SourceList sources={message.sources} />}
                    </>
                )}
            </div>
        </div>
    );
}