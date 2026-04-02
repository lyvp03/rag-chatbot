import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

// Hook quản lý theme
export function useTheme() {
    const [theme, setTheme] = useState<Theme>('dark');

    // Đọc localStorage chỉ trên client (tránh lỗi SSR)
    useEffect(() => {
        const saved = localStorage.getItem('theme') as Theme;
        if (saved) {
            setTheme(saved);
        }
    }, []);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    return { theme, toggleTheme };
}
