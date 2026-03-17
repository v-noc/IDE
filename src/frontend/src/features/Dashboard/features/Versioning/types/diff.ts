export type DiffType = "added" | "removed" | "modified" | "unchanged";

export type DiffNodeType =
  | "file"
  | "folder"
  | "function"
  | "class"
  | "document"
  | "code_content"
  | "group"
  | "project"
  | "call"
  | "unknown";

export interface NodeDiff {
  nodeId: string;
  nodeType: DiffNodeType;
  status: DiffType;
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  changes?: {
    field: string;
    oldValue: unknown;
    newValue: unknown;
  }[];
}

export interface ContentDiff {
  nodeId: string;
  contentType: "code" | "rich_text" | "structure";
  before: string | object | null;
  after: string | object | null;
  patches?: unknown[];
}

export interface DiffResult {
  commitBefore: string;
  commitAfter: string;
  nodeDiffs: NodeDiff[];
  contentDiffs: ContentDiff[];
  relationshipChanges: {
    added: Array<{ parent: string; child: string }>;
    removed: Array<{ parent: string; child: string }>;
  };
}

