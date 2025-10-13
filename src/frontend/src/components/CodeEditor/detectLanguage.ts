
export function detectLanguage(
    fileName: string
): string {

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


