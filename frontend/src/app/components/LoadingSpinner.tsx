// Loading spinner
export function LoadingSpinner() {
    return (
        <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-10 w-10 border-4 border-[var(--accent-color)] border-t-transparent"></div>
        </div>
    );
}
