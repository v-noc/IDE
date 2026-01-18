import { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useCode } from "@/services/code";
import { useEditableCode } from "./useEditableCode";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import CodeEditor from "@/components/CodeEditor";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";
import type { CallNodeTree } from "@/types/project";

interface EditorCodeProps {
  tabId: string;
}

const EditorCode = ({ tabId }: EditorCodeProps) => {
  const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
  const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode[tabId]);
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

  const elementId = effectiveNode?._key ?? "";
  const nodeType = effectiveNode?.node_type;
  const projectId = projectData?._key;
  const { data } = useCode(elementId, nodeType);
  const {
    editorValue,
    hasChanges,
    isLoading,
    isError,
    isSaving,
    handleEditorChange,
    handleSave,
  } = useEditableCode(elementId, projectId, nodeType);

  const language = useMemo(
    () => detectLanguage(data?.file_name || data?.file_path || ""),
    [data?.file_name, data?.file_path]
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
    </div>
  );
};

export default EditorCode;
