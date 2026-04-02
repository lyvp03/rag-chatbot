// Typing indicator
export function TypingIndicator() {
    return (
        <div className="flex mb-4 animate-fade-in">
            <div className="bg-[var(--bg-secondary)] rounded-2xl px-4 py-3 border border-[var(--border-color)]">
                <div className="flex items-center gap-2">
                    {/* Text "Đang suy nghĩ" với animation */}
                    <span className="text-[var(--text-secondary)] text-sm animate-pulse">
                        Đang suy nghĩ
                    </span>
                    {/* 3 chấm bounce */}
                    <div className="flex gap-1">
                        <span
                            className="w-1.5 h-1.5 bg-[var(--text-secondary)] rounded-full animate-bounce"
                            style={{ animationDelay: '0ms' }}
                        />
                        <span
                            className="w-1.5 h-1.5 bg-[var(--text-secondary)] rounded-full animate-bounce"
                            style={{ animationDelay: '150ms' }}
                        />
                        <span
                            className="w-1.5 h-1.5 bg-[var(--text-secondary)] rounded-full animate-bounce"
                            style={{ animationDelay: '300ms' }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
