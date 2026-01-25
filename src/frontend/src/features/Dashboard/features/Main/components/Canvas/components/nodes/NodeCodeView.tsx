import React, { memo, lazy, Suspense, useState } from "react";
import { Save, Copy, Check, Maximize2 } from "lucide-react";
import { CodeViewDialog } from "./CodeViewDialog";

// Lazy load Monaco Editor
const CodeEditor = lazy(() => import("@/components/CodeEditor"));

function CodeEditorSkeleton() {
  return (
    <div className="h-[300px] bg-slate-50 animate-pulse flex items-center justify-center border-b">
      <span className="text-slate-400 text-xs">Loading editor...</span>
    </div>
  );
}

interface NodeCodeViewProps {
  code: string;
  fileName: string;
  language: string;
  onChange: (value: string | undefined) => void;
  onSave: () => void;
  hasChanges: boolean;
  isSaving: boolean;
  isLoading: boolean;
  borderColor: string;
  iconColor: string;
}

export const NodeCodeView = memo(function NodeCodeView({
  code,
  fileName,
  language,
  onChange,
  onSave,
  hasChanges,
  isSaving,
  isLoading,
  borderColor,
  iconColor,
}: NodeCodeViewProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border-t bg-slate-50" style={{ borderColor }}>
      <div
        className="flex items-center justify-between px-4 py-2.5 bg-white border-b"
        style={{ borderColor }}
      >
        <span className="font-mono text-xs font-semibold text-slate-700 truncate max-w-[200px]">
          {fileName || "Code"}
        </span>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSave();
              }}
              disabled={isSaving}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all hover:bg-slate-100 active:scale-95 disabled:opacity-50"
              style={{ color: iconColor }}
            >
              <Save size={14} />
              <span>{isSaving ? "Saving..." : "Save"}</span>
            </button>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all hover:bg-slate-100 active:scale-95"
            style={{ color: iconColor }}
          >
            {copied ? (
              <>
                <Check size={14} />
                <span>Copied</span>
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
            onClick={() => setIsExpanded(true)}
            className="flex items-center justify-center p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <Maximize2 size={14} />
          </button>
        </div>
      </div>
      <CodeViewDialog
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        code={code}
        fileName={fileName}
        language={language}
        onChange={onChange}
        onSave={onSave}
        hasChanges={hasChanges}
        isSaving={isSaving}
        isLoading={isLoading}
        borderColor={borderColor}
        iconColor={iconColor}
      />
      <div
        className="h-[300px] mt-1 overflow-hidden border-b nodrag"
        style={{ borderColor }}
      >
        <Suspense fallback={<CodeEditorSkeleton />}>
          <CodeEditor
            language={language}
            value={code}
            onChange={onChange}
            isLoading={isLoading}
            options={{
              minimap: { enabled: false },
              readOnly: false,
              scrollBeyondLastLine: false,
              fontSize: 12,
              lineHeight: 18,
            }}
          />
        </Suspense>
      </div>
    </div >
  );
});
