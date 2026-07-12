import { useState } from "react";
import { useCode } from "@/services/code";
import { useEditableCode } from "@/features/Dashboard/features/Main/components/Code/useEditableCode";
import { useCodeDiff } from "@/features/Dashboard/features/Main/components/Code/useCodeDiff";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";

export interface UseNodeCodeOptions {
  nodeId: string;
  targetKey?: string;
  nodeType?: string;
}

export function useNodeCode({ nodeId, targetKey, nodeType }: UseNodeCodeOptions) {
  const [showCode, setShowCode] = useState(false);
  const { projectData } = useProjectStore();
  const projectId = projectData?.id;
  const walkthroughCodeOpen = useWalkthroughStore(
    (s) => s.phase === "playing" && s.codeOpenNodeId === nodeId,
  );

  // Only fetch code for file, class, or function node types
  const shouldFetchCode =
    nodeType === "file" || nodeType === "class" || nodeType === "function" || nodeType === "call";

  // Fetch code dynamically for the node
  const effectiveNodeId = nodeType === "call" && targetKey ? targetKey : nodeId;
  // For call nodes, use the target's node type, otherwise use the node's type
  const effectiveNodeType = nodeType === "call" ? "call" : nodeType;

  const { data: codeData } = useCode(
    (showCode || walkthroughCodeOpen) && shouldFetchCode ? effectiveNodeId : undefined,
    effectiveNodeType,
    projectId
  );

  const {
    editorValue,
    hasChanges,
    isLoading,
    isError,
    isSaving,
    handleEditorChange,
    handleSave,
  } = useEditableCode(
    shouldFetchCode ? effectiveNodeId : "",
    projectId,
    effectiveNodeType
  );
  const {
    showDiff,
    originalContent,
    modifiedContent,
    isLoadingDiff,
    error: diffError,
  } = useCodeDiff({
    codeData,
  });

  const hasCode =
    (codeData?.code && codeData.code.length > 0) ||
    (editorValue && editorValue.length > 0);

  const fileName = codeData?.file_name || codeData?.file_path || "";
  const language = detectLanguage(codeData?.file_path || codeData?.file_name || "");

  const toggleCode = () => setShowCode((prev) => !prev);

  const effectiveShowCode = showCode || walkthroughCodeOpen;
  const isWalkthroughPlaying = useWalkthroughStore((s) => s.phase === "playing");

  return {
    showCode: effectiveShowCode,
    toggleCode,
    hasCode,
    code: editorValue,
    setCode: handleEditorChange,
    hasChanges,
    isSaving,
    isLoading,
    isError,
    fileName,
    language,
    handleSave,
    showDiff,
    originalContent,
    modifiedContent,
    isLoadingDiff,
    diffError,
    nodeStartLine: codeData?.position?.line_no,
    isWalkthroughPlaying,
  };
}
