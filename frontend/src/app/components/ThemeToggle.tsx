import { useTheme } from '../hooks/useTheme';

// Toggle theme
export function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className="px-3 py-2 rounded-lg text-base transition-colors
        text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
            title={theme === 'dark' ? 'Chuyển sang Light mode' : 'Chuyển sang Dark mode'}
        >
            {theme === 'dark' ? 'Light' : 'Dark'}
        </button>
    );
}
