/** Params aligned with `vnoc_lsp_python.rpc` (Python driver). */

export type InitializeParams = {
  project_path: string;
  language?: string;
  config?: Record<string, unknown>;
};

export type ParseFileParams = {
  file_path: string;
  content: string;
  resolve_mro?: boolean;
};

export type ResolveCallsParams = {
  file_path: string;
  calls: Record<string, unknown>[];
};

export type ReadFileParams = {
  file_path: string;
};

export type ReadFolderParams = {
  folder_path: string;
};
