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
  const walkthroughForcesCode = useWalkthroughStore(
    (s) => Boolean(nodeId && s.forcedCodeOpen[nodeId]),
  );
  const { projectData } = useProjectStore();
  const projectId = projectData?.id;

  // Only fetch code for file, class, or function node types
  const shouldFetchCode =
    nodeType === "file" || nodeType === "class" || nodeType === "function";

  // Fetch code dynamically for the node
  const effectiveNodeId = nodeType === "call" && targetKey ? targetKey : nodeId;
  // For call nodes, use the target's node type, otherwise use the node's type
  const effectiveNodeType = nodeType === "call" ? "call" : nodeType;

  const revealCode = showCode || walkthroughForcesCode;

  const { data: codeData } = useCode(
    revealCode && shouldFetchCode ? effectiveNodeId : undefined,
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
  const language = detectLanguage(fileName);

  const toggleCode = () => setShowCode((prev) => !prev);

  return {
    showCode: revealCode,
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
  };
}
