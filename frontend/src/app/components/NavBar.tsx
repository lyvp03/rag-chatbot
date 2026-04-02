'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from './ThemeToggle'; // Lưu ý giữ nguyên nếu file này đang nằm cùng thư mục

export default function NavBar() {
    const pathname = usePathname();

    return (
        <nav className="fixed top-0 w-full z-10 border-b border-[var(--border-color)] bg-[var(--bg-primary)]/80 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    <div className="flex items-center">
                        <span className="text-lg sm:text-xl font-bold text-[var(--text-primary)]">RAG Chatbot</span>
                    </div>
                    <div className="flex items-center gap-1 sm:gap-2">

                        {/* Sử dụng Link của next/link thay cho NavLink */}
                        <Link
                            href="/"
                            className={`px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg text-sm sm:text-base transition-colors ${pathname === '/chat'
                                ? 'bg-[var(--bg-hover)] text-[var(--text-primary)]'
                                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]'
                                }`}
                        >
                            RAG Chatbot
                        </Link>

                        <ThemeToggle />
                    </div>
                </div>
            </div>
        </nav>
    );
}
