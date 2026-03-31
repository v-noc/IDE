import type {
  InitializeParams,
  ParseFileParams,
  ReadFileParams,
  ReadFolderParams,
  ResolveCallsParams,
} from "./types";

/**
 * Placeholder implementations — replace with real TS/JS driver logic later.
 * Return shapes mirror `PythonDriverService` in `vnoc_lsp_python.service`.
 */
export const mockDriver = {
  initialize(params: InitializeParams) {
    void params;
    return {
      status: "ok" as const,
      extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"],
    };
  },

  parseFile(params: ParseFileParams) {
    return {
      nodes: [] as unknown[],
      content: params.content,
      modified: false,
    };
  },

  resolveCalls(params: ResolveCallsParams) {
    void params;
    return {
      call_frame_stack: {
        target_qname: "root",
        target_id: "root",
        children: [] as unknown[],
      },
    };
  },

  readOrInjectFileId(params: ReadFileParams) {
    void params;
    return { file_id: "mock-file-id", modified: false };
  },

  readOrInjectFolderId(params: ReadFolderParams) {
    void params;
    return { folder_id: "mock-folder-id", modified: false };
  },

  shutdown(_params: Record<string, unknown> | null | undefined) {
    void _params;
    return { status: "ok" as const };
  },
};
