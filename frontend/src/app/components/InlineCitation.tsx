// src/app/components/InlineCitation.tsx
"use client";

import { useState, useRef, useEffect } from "react";
import type { SourceChunk } from "@/app/types/interfaces";

function cleanFilename(filename: string) {
    return filename.replace(/^[a-f0-9-]+_/, "");
}

function fileTypeLabel(type: string) {
    const map: Record<string, string> = {
        pdf: "PDF", txt: "TXT", md: "MD",
        mp3: "MP3", wav: "WAV",
    };
    return map[type.toLowerCase()] ?? type.toUpperCase();
}

function formatScore(score: number) {
    return `${Math.round(score * 100)}%`;
}

interface InlineCitationProps {
    indices: number[];
    sources: SourceChunk[];
}

export function InlineCitation({ indices, sources }: InlineCitationProps) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLSpanElement>(null);

    // Click outside → close
    useEffect(() => {
        if (!open) return;
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, [open]);

    const validSources = indices
        .map(i => sources[i])
        .filter(Boolean);

    if (!validSources.length) return null;

    return (
        <span ref={ref} className="relative inline-block">
            {/* Citation button */}
            <button
                onClick={() => setOpen(v => !v)}
                className={`inline-flex items-center gap-0.5 mx-0.5 px-1 py-0.5
                    rounded text-[10px] font-bold align-middle cursor-pointer
                    transition-all border
                    ${open
                        ? "bg-[var(--accent-color)] text-white border-[var(--accent-color)]"
                        : "bg-[var(--accent-color)]/10 text-[var(--accent-color)] border-[var(--accent-color)]/30 hover:bg-[var(--accent-color)]/20"
                    }`}
            >
                {indices.map(i => i + 1).join(",")}
            </button>

            {/* Popup */}
            {open && (
                <span className="absolute bottom-full left-0 mb-2 z-50 block w-72
                    bg-[var(--bg-secondary)] border border-[var(--input-border)]
                    rounded-xl shadow-xl overflow-hidden"
                >
                    {validSources.map((src, i) => (
                        <span key={i} className="block">
                            {/* Header */}
                            <span className="flex items-center gap-2 px-3 py-2
                                border-b border-[var(--input-border)] bg-[var(--input-bg)]"
                            >
                                <span className="text-[10px] font-bold px-1.5 py-0.5
                                    rounded bg-[var(--accent-color)]/20 text-[var(--accent-color)]"
                                >
                                    {fileTypeLabel(src.file_type)}
                                </span>
                                <span className="text-xs font-medium text-[var(--text-primary)] truncate flex-1">
                                    {cleanFilename(src.filename)}
                                </span>
                                <span className="text-xs text-[var(--text-secondary)] shrink-0">
                                    chunk #{src.chunk_index}
                                </span>
                            </span>

                            {/* Relevance bar */}
                            <span className="flex items-center gap-2 px-3 pt-2 pb-1">
                                <span className="text-[10px] text-[var(--text-secondary)]">
                                    Độ liên quan
                                </span>
                                <span className="flex-1 h-1 rounded-full bg-[var(--input-border)] overflow-hidden">
                                    <span
                                        className="block h-full rounded-full bg-[var(--accent-color)]"
                                        style={{ width: `${Math.round(src.relevance_score * 100)}%` }}
                                    />
                                </span>
                                <span className="text-[10px] font-medium text-[var(--accent-color)]">
                                    {formatScore(src.relevance_score)}
                                </span>
                            </span>

                            {/* Preview */}
                            <span className="block px-3 pb-3">
                                <span className="text-xs text-[var(--text-secondary)]
                                    leading-relaxed line-clamp-4"
                                >
                                    {src.content_preview}
                                </span>
                            </span>
                        </span>
                    ))}
                </span>
            )}
        </span>
    );
}