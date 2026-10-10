import { useMemo } from "react";
import { useTheme } from "next-themes";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useActiveCoverageForNode } from "@/features/Dashboard/store/useTestCoverageStore";
import { useCode } from "@/services/code";
import { useEditableCode } from "./useEditableCode";
import { useCodeDiff } from "./useCodeDiff";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import CodeEditor from "@/components/CodeEditor";
import { useCoverageHighlight } from "@/components/CodeEditor/useCoverageHighlight";
import CoverageSummary from "@/components/CodeEditor/CoverageSummary";
import { Button } from "@/components/ui/button";
import { DiffEditor } from "@monaco-editor/react";
import { Loader2, Save, Eye, EyeOff } from "lucide-react";
import type { CallNodeTree } from "@/types/project";

interface EditorCodeProps {
  tabId: string;
}

const EditorCode = ({ tabId }: EditorCodeProps) => {
  const { resolvedTheme } = useTheme();
  const monacoTheme = resolvedTheme === "light" ? "vs" : "vs-dark";
  const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
  const secondarySelectedNode = useProjectStore(
    (s) => s.secondarySelectedNode[tabId],
  );
  const projectData = useProjectStore((s) => s.projectData);
  const effectiveNode = useMemo(() => {
    if (secondarySelectedNode) {
      if ((secondarySelectedNode as CallNodeTree).target) {
        return (secondarySelectedNode as CallNodeTree).target;
      }
      return secondarySelectedNode;
    }
    if (selectedNode?.node_type === "call") {
      return selectedNode.target;
    }
    return selectedNode;
  }, [secondarySelectedNode, selectedNode]);

  const elementId = effectiveNode?.id ?? "";
  const nodeType = effectiveNode?.node_type;
  const projectId = projectData?.id ?? "";
  const { data } = useCode(elementId, nodeType, projectId);
  const coveredLines = useActiveCoverageForNode(tabId, elementId);
  const coverageStartLine = data?.position?.line_no ?? 1;
  const {
    onMount: coverageOnMount,
    hasCoverage,
    showCoverage,
    toggleCoverage,
  } = useCoverageHighlight(coveredLines, coverageStartLine);
  const {
    editorValue,
    hasChanges,
    isLoading,
    isError,
    isSaving,
    handleEditorChange,
    handleSave,
  } = useEditableCode(elementId, projectId, nodeType);
  const { showDiff, originalContent, modifiedContent, isLoadingDiff, error } =
    useCodeDiff({
      codeData: data,
    });

  const language = useMemo(
    () => detectLanguage((data?.file_path ?? data?.file_name) || ""),
    [data?.file_name, data?.file_path],
  );

  const codeLineCount = editorValue ? editorValue.split("\n").length : 0;
  const coveredCount = useMemo(() => {
    if (!showCoverage) return 0;
    const covered = new Set(coveredLines);
    let count = 0;
    for (let i = 0; i < codeLineCount; i++) {
      if (covered.has(coverageStartLine + i)) count++;
    }
    return count;
  }, [showCoverage, coveredLines, coverageStartLine, codeLineCount]);

  if (!elementId) {
    return (
      <div className="flex h-full w-full items-center justify-center text-muted-foreground">
        Select a node to view code
      </div>
    );
  }

  return (
    <div className="relative h-full w-full min-h-0 bg-(--background-color)">
      {showDiff ? (
        isLoadingDiff ? (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading historical file data...
          </div>
        ) : error ? (
          <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
            {error}
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
            }}
          />
        )
      ) : (
        <div className="h-full w-full flex flex-col min-h-0">
          {hasCoverage && (
            <div className="flex items-center justify-between gap-2 px-2 py-1.5 border-b border-border shrink-0">
              {showCoverage ? (
                <CoverageSummary
                  total={codeLineCount}
                  coveredCount={coveredCount}
                  className="flex-1 min-w-0"
                />
              ) : (
                <span className="text-xs text-muted-foreground">
                  Test coverage available for this function
                </span>
              )}
              <Button
                type="button"
                size="sm"
                variant={showCoverage ? "default" : "outline"}
                className="gap-1.5 text-xs shrink-0"
                onClick={toggleCoverage}
              >
                {showCoverage ? (
                  <EyeOff className="size-3.5" />
                ) : (
                  <Eye className="size-3.5" />
                )}
                {showCoverage ? "Hide coverage" : "Show coverage"}
              </Button>
            </div>
          )}
          <div className="relative flex-1 min-h-0">
            <CodeEditor
              language={language}
              value={editorValue}
              onChange={handleEditorChange}
              isLoading={isLoading}
              isError={isError}
              onMount={coverageOnMount}
            />
            {hasChanges && (
              <Button
                onClick={handleSave}
                disabled={isSaving}
                className="absolute bottom-4 right-4"
                variant="outline"
                size="sm"
              >
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? "Saving..." : "Save"}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EditorCode;
