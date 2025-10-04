import { useEffect, useMemo, useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useEditorCode } from "./useEditorCode";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import CodeEditor from "@/components/CodeEditor";

const EditorCode = () => {
  const { selectedNode } = useProjectStore();
  const elementId = selectedNode?._key ?? "";
  const nodeType = selectedNode?.node_type ?? "file";

  const { data, isLoading, isError } = useEditorCode(elementId, nodeType);

  const [editorValue, setEditorValue] = useState<string>("");

  useEffect(() => {
    setEditorValue(data?.code ?? "");
  }, [data?.code]);

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
    <CodeEditor
      language={language}
      value={editorValue}
      onChange={(value) => setEditorValue(value ?? "")}
      isLoading={isLoading}
      isError={isError}
    />
  );
};

export default EditorCode;
