import Editor from "@monaco-editor/react";
import { useEffect, useMemo, useState } from "react";
import {
  useGetCodeFromElement,
  useGetFileCode,
  type CodeElementResponse,
  type FileCodeResponse,
} from "../../../../service/useCodeElement";
import useProjectStore from "../../../../store/useProjectStore";

const EditorCode = () => {
  const { selectedNode } = useProjectStore();
  const elementId = selectedNode?.id ?? "";
  const nodeType = selectedNode?.type;

  const isFile = nodeType === "file";
  const {
    data: elementData,
    isLoading: isElementLoading,
    isError: isElementError,
  } = useGetCodeFromElement(!isFile ? elementId : "");
  const {
    data: fileData,
    isLoading: isFileLoading,
    isError: isFileError,
  } = useGetFileCode(isFile ? elementId : "");

  const data: FileCodeResponse | CodeElementResponse | undefined = isFile
    ? fileData
    : elementData;
  const isLoading = isFile ? isFileLoading : isElementLoading;
  const isError = isFile ? isFileError : isElementError;

  const [editorValue, setEditorValue] = useState<string>("");

  useEffect(() => {
    setEditorValue(data?.code ?? "");
  }, [data?.code]);

  const language = useMemo(() => {
    const fileName =
      (data as FileCodeResponse | CodeElementResponse | undefined)?.file_name ||
      (data as FileCodeResponse | CodeElementResponse | undefined)?.file_path ||
      "";
    const ext = fileName.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "ts":
      case "tsx":
        return "typescript";
      case "js":
      case "jsx":
        return "javascript";
      case "json":
        return "json";
      case "md":
        return "markdown";
      case "yml":
      case "yaml":
        return "yaml";
      case "sql":
        return "sql";
      case "py":
      default:
        return "python";
    }
  }, [data]);

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
