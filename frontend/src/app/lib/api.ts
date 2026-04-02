// src/app/lib/api.ts
// Cài thư viện: npm install @microsoft/fetch-event-source

import { fetchEventSource } from "@microsoft/fetch-event-source";
import type {
    HealthResponse,
    DocumentItem,
    UploadResponse,
    SourceChunk,
    ChatStreamCallbacks,
} from "@/app/types/interfaces";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// ─── 1. Health ────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<HealthResponse> {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
}

// ─── 2. Documents ─────────────────────────────────────────────────────────────

/** Upload file (pdf, txt, md, mp3, wav, m4a, webm) */
export async function uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${BASE_URL}/documents/upload`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail ?? `Upload failed: ${res.status}`);
    }

    return res.json();
}

/** Lấy danh sách tất cả tài liệu */
export async function getDocuments(): Promise<{
    documents: DocumentItem[];
    total: number;
}> {
    const res = await fetch(`${BASE_URL}/documents`);
    if (!res.ok) throw new Error(`Failed to fetch documents: ${res.status}`);
    return res.json();
}

/** Lấy trạng thái xử lý của một tài liệu */
export async function getDocumentStatus(docId: string): Promise<DocumentItem> {
    const res = await fetch(`${BASE_URL}/documents/${docId}/status`);
    if (!res.ok) throw new Error(`Failed to get status: ${res.status}`);
    return res.json();
}

/** Xóa tài liệu và toàn bộ chunks trong vector DB */
export async function deleteDocument(
    docId: string
): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/documents/${docId}`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error(`Failed to delete document: ${res.status}`);
    return res.json();
}

/** Poll trạng thái tài liệu cho đến khi completed hoặc failed */
export async function pollDocumentStatus(
    docId: string,
    onStatus?: (status: DocumentItem) => void,
    intervalMs = 2000,
    timeoutMs = 120_000
): Promise<DocumentItem> {
    const start = Date.now();

    return new Promise((resolve, reject) => {
        const timer = setInterval(async () => {
            try {
                const doc = await getDocumentStatus(docId);
                onStatus?.(doc);

                if (doc.status === "completed" || doc.status === "failed") {
                    clearInterval(timer);
                    resolve(doc);
                }

                if (Date.now() - start > timeoutMs) {
                    clearInterval(timer);
                    reject(new Error("Polling timeout"));
                }
            } catch (err) {
                clearInterval(timer);
                reject(err);
            }
        }, intervalMs);
    });
}

// ─── 3. Chat (SSE Streaming) ──────────────────────────────────────────────────

/**
 * Gửi câu hỏi và nhận trả lời dạng stream.
 *
 * @example
 * const stop = sendChatMessage("Bitcoin là gì?", {
 *   onSources: (sources) => console.log(sources),
 *   onToken:   (token)   => setAnswer(prev => prev + token),
 *   onDone:    ()        => setLoading(false),
 *   onError:   (err)     => console.error(err),
 * });
 *
 * // Hủy stream nếu cần:
 * stop();
 */
export function sendChatMessage(
    message: string,
    callbacks: ChatStreamCallbacks,
    topK = 5
): () => void {
    const controller = new AbortController();

    fetchEventSource(`${BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, top_k: topK }),
        signal: controller.signal,
        openWhenHidden: true,

        onmessage(event) {
            switch (event.event) {
                case "sources": {
                    try {
                        const sources: SourceChunk[] = JSON.parse(event.data);
                        callbacks.onSources?.(sources);
                    } catch {
                        // ignore parse error
                    }
                    break;
                }
                case "token": {
                    callbacks.onToken?.(event.data);
                    break;
                }
                case "done": {
                    callbacks.onDone?.();
                    controller.abort();
                    break;
                }
                case "error": {
                    try {
                        const err = JSON.parse(event.data);
                        callbacks.onError?.(err?.detail ?? event.data);
                    } catch {
                        callbacks.onError?.(event.data);
                    }
                    controller.abort();
                    break;
                }
            }
        },

        onerror(err) {
            callbacks.onError?.(err?.message ?? "Stream connection error");
            throw err; // dừng retry tự động
        },
    });

    return () => controller.abort();
}