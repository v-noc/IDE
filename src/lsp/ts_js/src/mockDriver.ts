import type { ReadFileParams, ReadFolderParams } from "./types";

/** Stubs for RPC methods not implemented in the TS/JS driver yet. */
export const mockDriver = {
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
