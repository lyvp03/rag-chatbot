"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import type { DragEvent } from "react";
import { uploadDocument, pollDocumentStatus } from "@/app/lib/api";
import type { DocumentItem } from "@/app/types/interfaces";

// ─── Types ────────────────────────────────────────────────────────────────────

export type UploadPhase =
    | { phase: "idle" }
    | { phase: "uploading"; filename: string; progress: number }
    | { phase: "processing"; filename: string }
    | { phase: "done"; filename: string }
    | { phase: "error"; filename: string; message: string };

const ACCEPTED_MIME = [
    "application/pdf",
    "text/plain",
    "text/markdown",
    "audio/mpeg",
    "audio/wav",
    "audio/x-m4a",
    "audio/webm",
    "video/webm",
];

function formatBytes(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ─── Icons ────────────────────────────────────────────────────────────────────

function XIcon() {
    return (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
    );
}

function UploadCloudIcon() {
    return (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
    );
}

function FileIcon() {
    return (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    );
}

function CheckIcon() {
    return (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
    );
}

function SpinnerIcon() {
    return (
        <svg className="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
    );
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface UploadModalProps {
    onClose: () => void;
    onUploadComplete?: (doc: DocumentItem) => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function UploadModal({ onClose, onUploadComplete }: UploadModalProps) {
    const [mounted, setMounted] = useState(false);
    const [dragging, setDragging] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [state, setState] = useState<UploadPhase>({ phase: "idle" });
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        setMounted(true);
    }, []);

    const handleFile = useCallback((file: File) => {
        if (!ACCEPTED_MIME.includes(file.type)) {
            setState({ phase: "error", filename: file.name, message: "Định dạng không hỗ trợ. Vui lòng dùng PDF, TXT, MD, MP3, WAV, M4A hoặc WEBM." });
            return;
        }
        setSelectedFile(file);
        setState({ phase: "idle" });
    }, []);

    const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    const handleUpload = async () => {
        if (!selectedFile) return;

        setState({ phase: "uploading", filename: selectedFile.name, progress: 0 });

        // Simulate upload progress
        let progress = 0;
        const progressTimer = setInterval(() => {
            progress = Math.min(progress + 15, 85);
            setState({ phase: "uploading", filename: selectedFile.name, progress });
        }, 200);

        try {
            const uploaded = await uploadDocument(selectedFile);
            clearInterval(progressTimer);

            setState({ phase: "processing", filename: selectedFile.name });

            const doc = await pollDocumentStatus(uploaded.id);

            if (doc.status === "completed") {
                setState({ phase: "done", filename: selectedFile.name });
                onUploadComplete?.(doc);
            } else {
                setState({
                    phase: "error",
                    filename: selectedFile.name,
                    message: doc.error_message ?? "Xử lý thất bại.",
                });
            }
        } catch (err) {
            clearInterval(progressTimer);
            setState({
                phase: "error",
                filename: selectedFile.name,
                message: err instanceof Error ? err.message : "Lỗi không xác định.",
            });
        }
    };

    const reset = () => {
        setSelectedFile(null);
        setState({ phase: "idle" });
    };

    const isDone = state.phase === "done";
    const isProcessing = state.phase === "uploading" || state.phase === "processing";

    if (!mounted) return null;

    return createPortal(
        // Backdrop
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="relative w-full max-w-md bg-[var(--bg-secondary)] rounded-2xl shadow-2xl border border-[var(--input-border)] overflow-hidden">

                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--input-border)]">
                    <h2 className="text-base font-semibold text-[var(--text-primary)]">Tải lên tài liệu</h2>
                    <button
                        onClick={onClose}
                        disabled={isProcessing}
                        className="p-1 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--input-bg)] transition-colors disabled:opacity-40"
                    >
                        <XIcon />
                    </button>
                </div>

                {/* Body */}
                <div className="p-5 space-y-4">

                    {/* Drop zone — chỉ hiện khi chưa chọn file hoặc idle */}
                    {!selectedFile && state.phase === "idle" && (
                        <div
                            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className={`flex flex-col items-center justify-center gap-3 p-8 rounded-xl border-2 border-dashed cursor-pointer transition-all
                ${dragging
                                    ? "border-[var(--accent-color)] bg-[var(--accent-color)]/10"
                                    : "border-[var(--input-border)] hover:border-[var(--accent-color)]/60 hover:bg-[var(--input-bg)]"
                                }`}
                        >
                            <span className="text-[var(--accent-color)]"><UploadCloudIcon /></span>
                            <div className="text-center">
                                <p className="text-sm font-medium text-[var(--text-primary)]">
                                    Kéo thả file vào đây
                                </p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1">
                                    hoặc <span className="text-[var(--accent-color)]">chọn file</span>
                                </p>
                            </div>
                            <p className="text-xs text-[var(--text-secondary)]">
                                PDF · TXT · MD · MP3 · WAV · M4A · WEBM
                            </p>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf,.txt,.md,.mp3,.wav,.m4a,.webm"
                                className="hidden"
                                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                            />
                        </div>
                    )}

                    {/* File đã chọn — idle */}
                    {selectedFile && state.phase === "idle" && (
                        <div className="flex items-center gap-3 p-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)]">
                            <span className="text-[var(--accent-color)]"><FileIcon /></span>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-[var(--text-primary)] truncate">{selectedFile.name}</p>
                                <p className="text-xs text-[var(--text-secondary)]">{formatBytes(selectedFile.size)}</p>
                            </div>
                            <button onClick={reset} className="p-1 rounded-md text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                                <XIcon />
                            </button>
                        </div>
                    )}

                    {/* Uploading */}
                    {state.phase === "uploading" && (
                        <div className="space-y-2 p-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)]">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-[var(--text-primary)] truncate">{state.filename}</span>
                                <span className="text-[var(--text-secondary)] ml-2">{state.progress}%</span>
                            </div>
                            <div className="h-1.5 rounded-full bg-[var(--input-border)] overflow-hidden">
                                <div
                                    className="h-full rounded-full bg-[var(--accent-color)] transition-all duration-300"
                                    style={{ width: `${state.progress}%` }}
                                />
                            </div>
                            <p className="text-xs text-[var(--text-secondary)]">Đang tải lên...</p>
                        </div>
                    )}

                    {/* Processing */}
                    {state.phase === "processing" && (
                        <div className="flex items-center gap-4 p-4 rounded-xl bg-[var(--input-bg)] border border-[var(--input-border)]">
                            <span className="text-[var(--accent-color)]"><SpinnerIcon /></span>
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">Đang xử lý tài liệu</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-0.5">Đang chunk và index vào Vector DB...</p>
                            </div>
                        </div>
                    )}

                    {/* Done */}
                    {state.phase === "done" && (
                        <div className="flex items-center gap-4 p-4 rounded-xl bg-green-500/10 border border-green-500/30">
                            <span className="text-green-500"><CheckIcon /></span>
                            <div>
                                <p className="text-sm font-medium text-[var(--text-primary)]">Tải lên thành công!</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-0.5 truncate">{state.filename}</p>
                            </div>
                        </div>
                    )}

                    {/* Error */}
                    {state.phase === "error" && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                            <p className="text-sm font-medium text-red-400">Lỗi</p>
                            <p className="text-xs text-red-300/80 mt-1">{state.message}</p>
                            <button onClick={reset} className="mt-2 text-xs text-[var(--accent-color)] hover:underline">
                                Thử lại
                            </button>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-[var(--input-border)]">
                    {isDone ? (
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--accent-color)] text-white hover:bg-[var(--accent-color)]/80 transition-colors"
                        >
                            Đóng
                        </button>
                    ) : (
                        <>
                            <button
                                onClick={onClose}
                                disabled={isProcessing}
                                className="px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--input-bg)] transition-colors disabled:opacity-40"
                            >
                                Hủy
                            </button>
                            <button
                                onClick={handleUpload}
                                disabled={!selectedFile || isProcessing}
                                className="px-4 py-2 rounded-lg text-sm font-medium 
                                    bg-[var(--accent-color,#3b82f6)] text-white 
                                    hover:opacity-80
                                    disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                                {isProcessing ? "Đang xử lý..." : "Tải lên"}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>,
        document.body
    );
}