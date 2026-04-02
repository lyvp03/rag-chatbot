import { useState, useEffect, useRef } from 'react';

interface UseTypingEffectOptions {
    text: string;
    speed?: number;
    enabled?: boolean;
}

interface UseTypingEffectResult {
    displayedText: string;
    isTyping: boolean;
    isComplete: boolean;
}

// Tính tốc độ typing để hoàn thành trong 2-5 giây
export function calculateSpeed(textLength: number): number {
    if (textLength <= 0) return 20;

    const minTime = 1000;
    const maxTime = 4000;
    const targetTime = Math.min(maxTime, Math.max(minTime, textLength * 15));
    const speed = Math.max(5, Math.min(50, targetTime / textLength));

    return speed;
}

// Hook hiệu ứng typing
export function useTypingEffect({
    text,
    speed,
    enabled = true,
}: UseTypingEffectOptions): UseTypingEffectResult {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);
    const indexRef = useRef(0);
    const timerRef = useRef<number | null>(null);

    // Tính speed tự động nếu không truyền
    const actualSpeed = speed ?? calculateSpeed(text.length);

    useEffect(() => {
        // Reset khi text thay đổi
        if (!enabled || !text) {
            setDisplayedText(text || '');
            setIsComplete(true);
            return;
        }

        // Reset state
        indexRef.current = 0;
        setDisplayedText('');
        setIsComplete(false);

        // Typing effect
        const tick = () => {
            if (indexRef.current < text.length) {
                indexRef.current += 1;
                setDisplayedText(text.slice(0, indexRef.current));
                timerRef.current = window.setTimeout(tick, actualSpeed);
            } else {
                setIsComplete(true);
            }
        };

        timerRef.current = window.setTimeout(tick, actualSpeed);

        // Cleanup
        return () => {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
        };
    }, [text, actualSpeed, enabled]);

    const isTyping = enabled && !isComplete && text.length > 0;

    return { displayedText, isTyping, isComplete };
}
