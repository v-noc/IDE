import { useEffect, useState } from "react";
import { useCode, useWriteCode } from "@/services/code";

export interface UseEditableCodeResult {
  editorValue: string;
  hasChanges: boolean;
  isLoading: boolean;
  isError: boolean;
  isSaving: boolean;
  handleEditorChange: (value: string | undefined) => void;
  handleSave: () => void;
  reset: () => void;
}

/**
 * Shared hook for managing editable code editor state, change tracking, and save functionality.
 * Can be used by both the main editor and node editors.
 */
export function useEditableCode(
  elementId: string,
  projectId?: string,
  nodeType?: string
): UseEditableCodeResult {
  const { data, isLoading, isError } = useCode(elementId, nodeType);
  const { mutate: saveCode, isPending: isSaving } = useWriteCode();

  const [editorValue, setEditorValue] = useState<string>("");
  const [hasChanges, setHasChanges] = useState(false);

  // Reset editor value when data changes
  useEffect(() => {
    const initialCode = data?.code ?? "";
    setEditorValue(initialCode);
    setHasChanges(false);
  }, [data?.code]);

  const handleEditorChange = (value: string | undefined) => {
    const newCode = value ?? "";
    setEditorValue(newCode);
    setHasChanges(newCode !== (data?.code ?? ""));
  };

  const handleSave = () => {
    if (hasChanges && !isSaving && elementId) {
      saveCode({ elementId, code: editorValue, projectId });
      setHasChanges(false);
    }
  };

  const reset = () => {
    const initialCode = data?.code ?? "";
    setEditorValue(initialCode);
    setHasChanges(false);
  };

  return {
    editorValue,
    hasChanges,
    isLoading,
    isError,
    isSaving,
    handleEditorChange,
    handleSave,
    reset,
  };
}

