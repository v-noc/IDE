import {
    useGetCodeForNode,

    useWriteCode,
    type CodeResponse,
} from "../../service/useCodeElement";
// nodeType intentionally unused now; we fetch both and pick best


export interface EditorCodeResult {
    data: CodeResponse | undefined;
    isLoading: boolean;
    isError: boolean;
    saveCode: (code: string) => void;
    isSaving: boolean;
}

/**
 * Decides which API to call based on node type and returns unified loading/error/data.
 * For virtual folders, it attempts file-code and element-code in parallel and prefers
 * whichever resolves successfully.
 */
export function useEditorCode(elementId: string): EditorCodeResult {
    // Try both endpoints defensively; prefer element code, fall back to file code

    const { data, isLoading, isError } = useGetCodeForNode(elementId || "");

    const { mutate: save, isPending: isSaving } = useWriteCode();

    const saveCode = (code: string) => {
        save({ elementId, code });
    }



    return { data, isLoading, isError, saveCode, isSaving };
}


