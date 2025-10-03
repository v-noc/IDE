import type { CodeResponse } from "../../../../service/useCodeElement";

export function detectLanguage(
    data: CodeResponse | undefined
): string {
    const fileName = data?.file_name || data?.file_path || "";
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
}


