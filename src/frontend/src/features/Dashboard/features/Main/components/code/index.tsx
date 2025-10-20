import { useEffect, useMemo, useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useEditorCode } from "./useEditorCode";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import CodeEditor from "@/components/CodeEditor";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";

const EditorCode = () => {
  const { selectedNode, secondarySelectedNode } = useProjectStore();
  const effectiveNode = useMemo(() => {
    if (secondarySelectedNode) {
      if (secondarySelectedNode.target) {
        return secondarySelectedNode.target;
      }
      return secondarySelectedNode;
    }
    return selectedNode;
  }, [secondarySelectedNode]);

  const elementId = effectiveNode?._key ?? "";
  const { data, isLoading, isError, saveCode, isSaving } =
    useEditorCode(elementId);

  const [editorValue, setEditorValue] = useState<string>("");
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const initialCode = data?.code ?? "";
    setEditorValue(initialCode);
    setHasChanges(false);
  }, [data?.code]);

  const language = useMemo(
    () => detectLanguage(data?.file_name || data?.file_path || ""),
    [data?.file_name, data?.file_path]
  );

  const handleEditorChange = (value: string | undefined) => {
    const newCode = value ?? "";
    setEditorValue(newCode);
    setHasChanges(newCode !== (data?.code ?? ""));
  };

  const handleSave = () => {
    saveCode(editorValue);
    setHasChanges(false);
  };

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
