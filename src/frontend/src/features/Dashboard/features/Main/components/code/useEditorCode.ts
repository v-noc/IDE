import { useMemo } from "react";
import {
    useGetCodeFromElement,
    useGetFileCode,
    type CodeElementResponse,
    type FileCodeResponse,
} from "../../../../service/useCodeElement";

type NodeType = "file" | "function" | "class" | "virtual_folder" | string | undefined;

export interface EditorCodeResult {
    data: FileCodeResponse | CodeElementResponse | undefined;
    isLoading: boolean;
    isError: boolean;
}

/**
 * Decides which API to call based on node type and returns unified loading/error/data.
 * For virtual folders, it attempts file-code and element-code in parallel and prefers
 * whichever resolves successfully.
 */
export function useEditorCode(elementId: string, nodeType: NodeType): EditorCodeResult {
    const isFile = nodeType === "file";
    const isCodeElement = nodeType === "function" || nodeType === "class";
    const isVirtualFolder = nodeType === "virtual_folder";

    // File nodes → only file-code
    const fileQuery = useGetFileCode(isFile || isVirtualFolder ? elementId : "");

    // Function/Class nodes → only element-code
    const elementQuery = useGetCodeFromElement(
        isCodeElement || isVirtualFolder ? elementId : ""
    );

    const { data, isLoading, isError } = useMemo(() => {
        // File nodes
        if (isFile) {
            return {
                data: fileQuery.data,
                isLoading: fileQuery.isLoading,
                isError: fileQuery.isError,
            };
        }

        // Code element nodes
        if (isCodeElement) {
            return {
                data: elementQuery.data,
                isLoading: elementQuery.isLoading,
                isError: elementQuery.isError,
            };
        }

        // Virtual folder: prefer whichever succeeded; otherwise wait until both settle
        if (isVirtualFolder) {
            const data = fileQuery.data ?? elementQuery.data;
            const isLoading = fileQuery.isLoading || elementQuery.isLoading;
            const isError =
                !isLoading &&
                Boolean(fileQuery.error) &&
                Boolean(elementQuery.error) &&
                !data;
            return { data, isLoading, isError };
        }

        // Fallback
        return { data: undefined, isLoading: false, isError: true };
    }, [
        isFile,
        isCodeElement,
        isVirtualFolder,
        fileQuery.data,
        fileQuery.isLoading,
        fileQuery.isError,
        fileQuery.error,
        elementQuery.data,
        elementQuery.isLoading,
        elementQuery.isError,
        elementQuery.error,
    ]);

    return { data, isLoading, isError };
}


