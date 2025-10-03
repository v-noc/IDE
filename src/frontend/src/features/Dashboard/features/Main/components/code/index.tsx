import Editor from "@monaco-editor/react";
import { useEffect, useMemo, useState } from "react";
import useProjectStore from "../../../../store/useProjectStore";
import { useEditorCode } from "./useEditorCode";
import { detectLanguage } from "./detectLanguage";

const EditorCode = () => {
  const { selectedNode } = useProjectStore();
  const elementId = selectedNode?._key ?? "";
  const nodeType = selectedNode?.node_type;

  const { data, isLoading, isError } = useEditorCode(elementId, nodeType);

  const [editorValue, setEditorValue] = useState<string>("");

  useEffect(() => {
    setEditorValue(data?.code ?? "");
  }, [data?.code]);

  const language = useMemo(() => detectLanguage(data), [data]);

  if (!elementId) {
    return (
      <div className="flex h-full w-full items-center justify-center text-muted-foreground">
        Select a node to view code
      </div>
    );
  }

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError) {
    return (
      <div className="flex h-full w-full items-center justify-center text-red-500">
        Failed to load code
      </div>
    );
  }

  return (
    <Editor
      className="h-full w-full"
      language={language}
      value={editorValue}
      onChange={(value) => setEditorValue(value ?? "")}
      options={{
        minimap: { enabled: false },
        wordWrap: "on",
        scrollBeyondLastLine: false,
      }}
    />
  );
};

export default EditorCode;
