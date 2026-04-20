import { memo, lazy, Suspense, useState } from "react";
import { useTheme } from "next-themes";
import { Save, Copy, Check, X } from "lucide-react";
import { DiffEditor } from "@monaco-editor/react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

// Lazy load Monaco Editor
const CodeEditor = lazy(() => import("@/components/CodeEditor"));

function CodeEditorSkeleton() {
    return (
        <div className="h-full w-full bg-muted animate-pulse flex items-center justify-center">
            <span className="text-muted-foreground text-sm">Loading editor...</span>
        </div>
    );
}

interface CodeViewDialogProps {
    isOpen: boolean;
    onClose: () => void;
    code: string;
    fileName: string;
    language: string;
    onChange: (value: string | undefined) => void;
    onSave: () => void;
    hasChanges: boolean;
    isSaving: boolean;
    isLoading: boolean;
    showDiff?: boolean;
    originalContent?: string;
    modifiedContent?: string;
    isLoadingDiff?: boolean;
    diffError?: string | null;
    borderColor?: string;
    iconColor?: string;
}

export const CodeViewDialog = memo(function CodeViewDialog({
    isOpen,
    onClose,
    code,
    fileName,
    language,
    onChange,
    onSave,
    hasChanges,
    isSaving,
    isLoading,
    showDiff = false,
    originalContent = "",
    modifiedContent = "",
    isLoadingDiff = false,
    diffError = null,
    borderColor: _borderColor = "#e2e8f0",
    iconColor = "#64748b",
}: CodeViewDialogProps) {
    void _borderColor;
    const { resolvedTheme } = useTheme();
    const monacoTheme = resolvedTheme === "light" ? "vs" : "vs-dark";
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(showDiff ? modifiedContent : code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="min-w-[60vw] w-full h-[90vh] flex flex-col p-0 gap-0 border border-border shadow-2xl overflow-hidden bg-card sm:rounded-xl">
                <DialogHeader className="px-5 py-3 border-b border-border flex flex-row items-center justify-between space-y-0 bg-card z-10">
                    <DialogTitle className="flex items-center gap-2">
                        <span className="font-mono text-sm font-semibold text-foreground">
                            {fileName || "Code Editor"}
                        </span>
                        {hasChanges && (
                            <span className="w-2 h-2 rounded-full bg-yellow-400" />
                        )}
                    </DialogTitle>

                    <div className="flex items-center gap-2">
                        {!showDiff && hasChanges && (
                            <button
                                onClick={onSave}
                                disabled={isSaving}
                                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all hover:bg-muted active:scale-95 disabled:opacity-50 border border-border"
                                style={{ color: iconColor }}
                            >
                                <Save size={14} />
                                <span>{isSaving ? "Saving..." : "Save Changes"}</span>
                            </button>
                        )}

                        <button
                            onClick={handleCopy}
                            className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all hover:bg-muted active:scale-95 border border-border"
                            style={{ color: iconColor }}
                        >
                            {copied ? (
                                <>
                                    <Check size={14} className="text-green-500" />
                                    <span className="text-green-600">Copied</span>
                                </>
                            ) : (
                                <>
                                    <Copy size={14} />
                                    <span>Copy</span>
                                </>
                            )}
                        </button>

                        <div className="w-px h-4 bg-border mx-1" />

                        <button
                            onClick={onClose}
                            className="flex items-center justify-center w-7 h-7 rounded-md text-muted-foreground transition-all hover:bg-muted hover:text-foreground"
                        >
                            <X size={16} />
                        </button>
                    </div>
                </DialogHeader>

                <div className="flex-1 min-h-0 bg-background relative w-full">
                    <Suspense fallback={<CodeEditorSkeleton />}>
                        {showDiff ? (
                            isLoadingDiff ? (
                                <CodeEditorSkeleton />
                            ) : diffError ? (
                                <div className="h-full w-full flex items-center justify-center text-sm text-muted-foreground">
                                    {diffError}
                                </div>
                            ) : (
                                <DiffEditor
                                    height="100%"
                                    language={language}
                                    original={originalContent}
                                    modified={modifiedContent}
                                    theme={monacoTheme}
                                    options={{
                                        readOnly: true,
                                        originalEditable: false,
                                        renderSideBySide: true,
                                        automaticLayout: true,
                                        minimap: { enabled: false },
                                        scrollBeyondLastLine: false,
                                        fontSize: 14,
                                        lineHeight: 22,
                                    }}
                                />
                            )
                        ) : (
                            <CodeEditor
                                language={language}
                                value={code}
                                onChange={onChange}
                                isLoading={isLoading}
                                options={{
                                    minimap: { enabled: true },
                                    readOnly: false,
                                    scrollBeyondLastLine: false,
                                    fontSize: 14,
                                    lineHeight: 22,
                                    padding: { top: 16, bottom: 16 },
                                    automaticLayout: true,
                                }}
                            />
                        )}
                    </Suspense>
                </div>
            </DialogContent>
        </Dialog>
    );
});
