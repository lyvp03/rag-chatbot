// src/app/lib/parseCitations.ts

import type { SourceChunk } from "@/app/types/interfaces";

export interface TextSegment {
    type: "text" | "citation";
    content: string;
    indices?: number[];   // [1][2] → [0, 1] (0-indexed)
}

export function parseCitations(text: string): TextSegment[] {
    const segments: TextSegment[] = [];
    // Match [1], [2], [1][2], [1][2][3]...
    const regex = /(\[\d+\])+/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
        // Text trước citation
        if (match.index > lastIndex) {
            segments.push({
                type: "text",
                content: text.slice(lastIndex, match.index),
            });
        }

        // Parse số trong [1][2] → [0, 1]
        const nums = [...match[0].matchAll(/\[(\d+)\]/g)]
            .map(m => parseInt(m[1]) - 1)  // convert sang 0-indexed
            .filter(n => n >= 0);

        segments.push({
            type: "citation",
            content: match[0],
            indices: nums,
        });

        lastIndex = match.index + match[0].length;
    }

    // Text còn lại
    if (lastIndex < text.length) {
        segments.push({
            type: "text",
            content: text.slice(lastIndex),
        });
    }

    return segments;
}