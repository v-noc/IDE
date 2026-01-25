import React, { memo, lazy, Suspense, useState, useEffect } from "react";
import { Save, Copy, Check, X } from "lucide-react";
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
        <div className="h-full w-full bg-slate-50 animate-pulse flex items-center justify-center">
            <span className="text-slate-400 text-sm">Loading editor...</span>
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
    borderColor = "#e2e8f0",
    iconColor = "#64748b",
}: CodeViewDialogProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="min-w-[60vw] w-full h-[90vh] flex flex-col p-0 gap-0 border-none shadow-2xl overflow-hidden bg-white sm:rounded-xl">
                <DialogHeader className="px-5 py-3 border-b flex flex-row items-center justify-between space-y-0 bg-white z-10">
                    <DialogTitle className="flex items-center gap-2">
                        <span className="font-mono text-sm font-semibold text-slate-700">
                            {fileName || "Code Editor"}
                        </span>
                        {hasChanges && (
                            <span className="w-2 h-2 rounded-full bg-yellow-400" />
                        )}
                    </DialogTitle>

                    <div className="flex items-center gap-2">
                        {hasChanges && (
                            <button
                                onClick={onSave}
                                disabled={isSaving}
                                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all hover:bg-slate-100 active:scale-95 disabled:opacity-50 border border-slate-200"
                                style={{ color: iconColor }}
                            >
                                <Save size={14} />
                                <span>{isSaving ? "Saving..." : "Save Changes"}</span>
                            </button>
                        )}

                        <button
                            onClick={handleCopy}
                            className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all hover:bg-slate-100 active:scale-95 border border-slate-200"
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

                        <div className="w-px h-4 bg-slate-200 mx-1" />

                        <button
                            onClick={onClose}
                            className="flex items-center justify-center w-7 h-7 rounded-md text-slate-400 transition-all hover:bg-slate-100 hover:text-slate-600"
                        >
                            <X size={16} />
                        </button>
                    </div>
                </DialogHeader>

                <div className="flex-1 min-h-0 bg-slate-50 relative w-full">
                    <Suspense fallback={<CodeEditorSkeleton />}>
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
                    </Suspense>
                </div>
            </DialogContent>
        </Dialog>
    );
});
