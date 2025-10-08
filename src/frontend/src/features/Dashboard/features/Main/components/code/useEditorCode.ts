import { useMemo } from "react";
import {
    useGetCodeForNode,
    useGetFileCode,
    useWriteCode,
    type CodeResponse,
} from "@/features/Dashboard/service/useCodeElement";
import type { NodeType } from "@/types/project";


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
export function useEditorCode(elementId: string, nodeType: NodeType): EditorCodeResult {
    const isFile = nodeType === "file";
    const isCodeElement = nodeType === "function" || nodeType === "class" || nodeType === "call";
    // const isVirtualFolder = nodeType === "virtual_folder";

    // File nodes → only file-code
    const fileQuery = useGetFileCode(isFile ? elementId : "");

    // Code element nodes → use unified code endpoint
    const elementQuery = useGetCodeForNode(
        isCodeElement ? elementId : ""
    );

    const { mutate: save, isPending: isSaving } = useWriteCode();

    const saveCode = (code: string) => {
        save({ elementId, code });
    }

    const { data, isLoading, isError } = useMemo(() => {
        // File nodes
        if (isFile) {
            return {
                data: fileQuery.data,
                isLoading: fileQuery.isLoading,
                isError: fileQuery.isError,
            };
        }

        // Code element nodes (function/class/call)
        if (isCodeElement) {
            return {
                data: elementQuery.data,
                isLoading: elementQuery.isLoading,
                isError: elementQuery.isError,
            };
        }

        // Virtual folder: prefer whichever succeeded; otherwise wait until both settle
        // if (isVirtualFolder) {
        //     const data = fileQuery.data ?? elementQuery.data;
        //     const isLoading = fileQuery.isLoading || elementQuery.isLoading;
        //     const isError =
        //         !isLoading &&
        //         Boolean(fileQuery.error) &&
        //         Boolean(elementQuery.error) &&
        //         !data;
        //     return { data, isLoading, isError };
        // }

        // Fallback
        return { data: undefined, isLoading: false, isError: true };
    }, [
        isFile,
        isCodeElement,
        fileQuery.data,
        fileQuery.isLoading,
        fileQuery.isError,
        elementQuery.data,
        elementQuery.isLoading,
        elementQuery.isError,
    ]);

    return { data, isLoading, isError, saveCode, isSaving };
}


