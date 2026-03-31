import { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useCode } from "@/services/code";
import { useEditableCode } from "./useEditableCode";
import { useCodeDiff } from "./useCodeDiff";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import CodeEditor from "@/components/CodeEditor";
import { Button } from "@/components/ui/button";
import { DiffEditor } from "@monaco-editor/react";
import { Loader2, Save } from "lucide-react";
import type { CallNodeTree } from "@/types/project";

interface EditorCodeProps {
  tabId: string;
}

const EditorCode = ({ tabId }: EditorCodeProps) => {
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

  if (!elementId) {
    return (
      <div className="flex h-full w-full items-center justify-center text-muted-foreground">
        Select a node to view code
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
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
            theme="vs-light"
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
        <>
          <CodeEditor
            language={language}
            value={editorValue}
            onChange={handleEditorChange}
            isLoading={isLoading}
            isError={isError}
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
        </>
      )}
    </div>
  );
};

export default EditorCode;
