interface WorkspaceHeaderProps {
    displayPath: string;
    suffixName: string;
    onPromote: () => void;
}

/**
 * Presentational component for the Workspace Header.
 * Displays the current path and 'promote' action for secondary selections.
 */
export function WorkspaceHeader({ displayPath, suffixName, onPromote }: WorkspaceHeaderProps) {
    return (
        <div className="px-2 text-xs text-muted-foreground truncate">
            {displayPath || "No selection"}
            {suffixName && (
                <>
                    {" "}
                    <button
                        type="button"
                        className="underline hover:no-underline cursor-pointer"
                        onClick={onPromote}
                    >
                        (promote)
                    </button>
                </>
            )}
        </div>
    );
}
