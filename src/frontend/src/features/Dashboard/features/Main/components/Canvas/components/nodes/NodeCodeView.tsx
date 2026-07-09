import React, { memo, lazy, Suspense, useState } from "react";
import { useTheme } from "next-themes";
import { Save, Copy, Check, Maximize2 } from "lucide-react";
import { DiffEditor, type Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { CodeViewDialog } from "./CodeViewDialog";
import { useWalkthroughMonaco } from "@/features/Dashboard/features/Agent/walkthrough/hooks/useWalkthroughMonaco";

// Lazy load Monaco Editor
const CodeEditor = lazy(() => import("@/components/CodeEditor"));

function CodeEditorSkeleton() {
  return (
    <div className="h-[300px] bg-muted animate-pulse flex items-center justify-center border-b border-border">
      <span className="text-muted-foreground text-xs">Loading editor...</span>
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
  showDiff?: boolean;
  originalContent?: string;
  modifiedContent?: string;
  isLoadingDiff?: boolean;
  diffError?: string | null;
  borderColor: string;
  iconColor: string;
  nodeId?: string;
  nodeStartLine?: number;
  isWalkthroughPlaying?: boolean;
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
  showDiff = false,
  originalContent = "",
  modifiedContent = "",
  isLoadingDiff = false,
  diffError = null,
  borderColor,
  iconColor,
  nodeId = "",
  nodeStartLine,
  isWalkthroughPlaying = false,
}: NodeCodeViewProps) {
  const { resolvedTheme } = useTheme();
  const monacoTheme = resolvedTheme === "light" ? "vs" : "vs-dark";
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const codeLoaded = !isLoading && code.length > 0;

  const { onMount: walkthroughOnMount } = useWalkthroughMonaco(
    nodeId,
    nodeStartLine,
    showDiff,
    codeLoaded,
  );

  const handleEditorMount = (
    editorInstance: editor.IStandaloneCodeEditor,
    monacoApi: Monaco,
  ) => {
    walkthroughOnMount(editorInstance, monacoApi);
  };

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(showDiff ? modifiedContent : code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border-t bg-muted/30" style={{ borderColor }}>
      <div
        className="flex items-center justify-between px-4 py-2.5 bg-card border-b border-border"
        style={{ borderColor }}
      >
        <span className="font-mono text-xs font-semibold text-foreground truncate max-w-[200px]">
          {fileName || "Code"}
        </span>
        <div className="flex items-center gap-2">
          {!showDiff && hasChanges && !isWalkthroughPlaying && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSave();
              }}
              disabled={isSaving}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all hover:bg-muted active:scale-95 disabled:opacity-50"
              style={{ color: iconColor }}
            >
              <Save size={14} />
              <span>{isSaving ? "Saving..." : "Save"}</span>
            </button>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all hover:bg-muted active:scale-95"
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
          <div className="w-px h-4 bg-border mx-1" />
          <button
            onClick={() => setIsExpanded(true)}
            className="flex items-center justify-center p-1.5 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
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
        showDiff={showDiff}
        originalContent={originalContent}
        modifiedContent={modifiedContent}
        isLoadingDiff={isLoadingDiff}
        diffError={diffError}
        borderColor={borderColor}
        iconColor={iconColor}
      />
      <div
        className="h-[300px] mt-1 overflow-hidden border-b nodrag"
        style={{ borderColor }}
      >
        <Suspense fallback={<CodeEditorSkeleton />}>
          {showDiff ? (
            isLoadingDiff ? (
              <CodeEditorSkeleton />
            ) : diffError ? (
              <div className="h-full w-full flex items-center justify-center text-xs text-muted-foreground">
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
                  fontSize: 12,
                  lineHeight: 18,
                }}
              />
            )
          ) : (
            <CodeEditor
              language={language}
              value={code}
              onChange={onChange}
              isLoading={isLoading}
              onMount={handleEditorMount}
              options={{
                minimap: { enabled: false },
                readOnly: isWalkthroughPlaying,
                scrollBeyondLastLine: false,
                fontSize: 12,
                lineHeight: 18,
              }}
            />
          )}
        </Suspense>
      </div>
    </div>
  );
});
