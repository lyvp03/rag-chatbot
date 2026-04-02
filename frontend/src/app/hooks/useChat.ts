// src/app/hooks/useChat.ts

import { useState, useCallback, useRef } from "react";
import { sendChatMessage } from "@/app/lib/api";
import type { SourceChunk } from "@/app/types/interfaces";

export type MessageRole = "user" | "assistant";

export interface Message {
    id: string;
    role: MessageRole;
    content: string;
    sources?: SourceChunk[];
    isStreaming?: boolean;
}

interface UseChatReturn {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    sendMessage: (text: string, topK?: number) => void;
    stopStreaming: () => void;
    clearMessages: () => void;
}

export function useChat(): UseChatReturn {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const stopRef = useRef<(() => void) | null>(null);

    const sendMessage = useCallback((text: string, topK = 5) => {
        if (!text.trim() || isLoading) return;

        setError(null);

        // Thêm message của user
        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: text.trim(),
        };

        // Placeholder cho assistant (sẽ được cập nhật dần qua stream)
        const assistantId = crypto.randomUUID();
        const assistantMessage: Message = {
            id: assistantId,
            role: "assistant",
            content: "",
            sources: [],
            isStreaming: true,
        };

        setMessages((prev) => [...prev, userMessage, assistantMessage]);
        setIsLoading(true);

        const stop = sendChatMessage(
            text.trim(),
            {
                onSources(sources) {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId ? { ...m, sources } : m
                        )
                    );
                },

                onToken(token) {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? { ...m, content: m.content + token }
                                : m
                        )
                    );
                },

                onDone() {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId ? { ...m, isStreaming: false } : m
                        )
                    );
                    setIsLoading(false);
                    stopRef.current = null;
                },

                onError(err) {
                    setError(err);
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? { ...m, isStreaming: false, content: m.content || "Đã xảy ra lỗi." }
                                : m
                        )
                    );
                    setIsLoading(false);
                    stopRef.current = null;
                },
            },
            topK
        );

        stopRef.current = stop;
    }, [isLoading]);

    const stopStreaming = useCallback(() => {
        stopRef.current?.();
        stopRef.current = null;
        setIsLoading(false);
        // Đánh dấu message cuối không còn streaming
        setMessages((prev) =>
            prev.map((m, i) =>
                i === prev.length - 1 ? { ...m, isStreaming: false } : m
            )
        );
    }, []);

    const clearMessages = useCallback(() => {
        stopRef.current?.();
        stopRef.current = null;
        setMessages([]);
        setIsLoading(false);
        setError(null);
    }, []);

    return {
        messages,
        isLoading,
        error,
        sendMessage,
        stopStreaming,
        clearMessages,
    };
}