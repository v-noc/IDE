import type { TerminusJsonDiff } from "@/services/versioning";
import type { ContentDiff, DiffResult, DiffType, DiffNodeType, NodeDiff } from "../types/diff";

const CHILD_SET_FIELDS = new Set([
  "folder_children",
  "file_children",
  "structure_group",
  "class_children",
  "function_children",
  "code_element_group",
  "call_group",
  "call_children",
]);

const CONTENT_FIELDS = new Set(["content", "data", "text", "source_code", "code"]);

type DiffCtx = {
  currentNodeId: string | null;
  currentField: string | null;
};

type NodeRef = {
  id: string;
};

type MutableAcc = {
  nodeDiffs: Map<string, NodeDiff>;
  contentDiffs: Map<string, ContentDiff>;
  relationshipAddedSet: Set<string>;
  relationshipRemovedSet: Set<string>;
  relationshipChanges: DiffResult["relationshipChanges"];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readId(value: Record<string, unknown>): string | null {
  if (typeof value["@id"] === "string") return value["@id"];
  if (typeof value.id === "string") return value.id;
  if (typeof value._id === "string") return value._id;
  return null;
}

function extractSchemaTypeName(raw: string): string {
  const compact = raw.trim();
  const slashToken = compact.split("/").pop() ?? compact;
  const hashToken = slashToken.split("#").pop() ?? slashToken;
  const colonToken = hashToken.split(":").pop() ?? hashToken;
  return colonToken.toLowerCase();
}

function toDiffNodeType(typeValue: unknown): DiffNodeType {
  if (typeof typeValue !== "string" || typeValue.trim() === "") return "unknown";
  const normalized = extractSchemaTypeName(typeValue);
  if (normalized.includes("codecontentschema")) return "code_content";
  if (normalized.includes("code_content")) return "code_content";
  if (normalized.includes("codecontent")) return "code_content";
  if (normalized.includes("document")) return "document";
  if (normalized.includes("project")) return "project";
  if (normalized.includes("folder")) return "folder";
  if (normalized.includes("file")) return "file";
  if (normalized.includes("function")) return "function";
  if (normalized.includes("class")) return "class";
  if (normalized.includes("call")) return "call";
  if (normalized.includes("group")) return "group";
  return "unknown";
}

function toNodeRef(value: unknown): NodeRef | null {
  if (typeof value === "string") return { id: value };
  if (!isRecord(value)) return null;
  const id = readId(value);
  if (!id) return null;
  return { id };
}

function toNodeRefList(value: unknown): NodeRef[] {
  if (Array.isArray(value)) {
    return value
      .map(toNodeRef)
      .filter((entry): entry is NodeRef => entry !== null);
  }
  const ref = toNodeRef(value);
  return ref ? [ref] : [];
}

function mergeStatus(current: DiffType, next: Exclude<DiffType, "unchanged">): DiffType {
  if (current === "unchanged") return next;
  if (current === next) return current;
  return "modified";
}

function upsertNodeDiff(
  acc: MutableAcc,
  nodeId: string,
  status: Exclude<DiffType, "unchanged">,
  patch?: Partial<NodeDiff>
) {
  const existing = acc.nodeDiffs.get(nodeId);
  if (!existing) {
    acc.nodeDiffs.set(nodeId, {
      nodeId,
      nodeType: patch?.nodeType ?? "unknown",
      status,
      before: patch?.before,
      after: patch?.after,
      changes: patch?.changes,
    });
    return;
  }
  acc.nodeDiffs.set(nodeId, {
    ...existing,
    ...patch,
    status: mergeStatus(existing.status, status),
    changes: patch?.changes ? [...(existing.changes ?? []), ...patch.changes] : existing.changes,
  });
}

function addRelationshipChange(
  acc: MutableAcc,
  type: "added" | "removed",
  parent: string,
  child: string
) {
  const key = `${parent}:${child}`;
  if (type === "added") {
    if (acc.relationshipAddedSet.has(key)) return;
    acc.relationshipAddedSet.add(key);
    acc.relationshipChanges.added.push({ parent, child });
    return;
  }
  if (acc.relationshipRemovedSet.has(key)) return;
  acc.relationshipRemovedSet.add(key);
  acc.relationshipChanges.removed.push({ parent, child });
}

function toContentType(field: string, nodeType: DiffNodeType): ContentDiff["contentType"] {
  if (field === "data") return "rich_text";
  if (nodeType === "code_content") return "code";
  if (field === "content" || field === "source_code" || field === "code") return "code";
  return "structure";
}

function setContentDiff(
  acc: MutableAcc,
  nodeId: string,
  contentType: ContentDiff["contentType"],
  before: unknown,
  after: unknown
) {
  acc.contentDiffs.set(nodeId, {
    nodeId,
    contentType,
    before: (before as string | object | null) ?? null,
    after: (after as string | object | null) ?? null,
  });
}

function handleInsertDelete(opObject: Record<string, unknown>, acc: MutableAcc) {
  const op = opObject["@op"];
  const payload = op === "Insert" ? opObject["@insert"] : opObject["@delete"];
  if (!isRecord(payload)) return;
  const nodeId = readId(payload);
  if (!nodeId) return;
  const nodeType = toDiffNodeType(payload["@type"]);
  if (op === "Insert") {
    upsertNodeDiff(acc, nodeId, "added", { nodeType, after: payload });
    if (nodeType === "code_content" && typeof payload.content === "string") {
      setContentDiff(acc, nodeId, "code", null, payload.content);
    }
    return;
  }
  upsertNodeDiff(acc, nodeId, "removed", { nodeType, before: payload });
  if (nodeType === "code_content" && typeof payload.content === "string") {
    setContentDiff(acc, nodeId, "code", payload.content, null);
  }
}

function handleChildSetOperation(
  opObject: Record<string, unknown>,
  currentNodeId: string,
  acc: MutableAcc
) {
  let cursor: unknown = opObject;
  let beforeList: NodeRef[] = [];
  let afterList: NodeRef[] = [];

  // Handle nested list patches, e.g. CopyList -> @rest -> SwapList.
  while (isRecord(cursor)) {
    const maybeBefore = toNodeRefList(cursor["@before"]);
    const maybeAfter = toNodeRefList(cursor["@after"]);
    if (maybeBefore.length > 0 || maybeAfter.length > 0) {
      beforeList = maybeBefore;
      afterList = maybeAfter;
      break;
    }
    cursor = cursor["@rest"];
  }

  const before = new Set(beforeList.map((entry) => entry.id));
  const after = new Set(afterList.map((entry) => entry.id));
  for (const id of after) {
    if (before.has(id)) continue;
    addRelationshipChange(acc, "added", currentNodeId, id);
    upsertNodeDiff(acc, id, "added");
  }
  for (const id of before) {
    if (after.has(id)) continue;
    addRelationshipChange(acc, "removed", currentNodeId, id);
    upsertNodeDiff(acc, id, "removed");
  }
  upsertNodeDiff(acc, currentNodeId, "modified");
}

function handleOperation(opObject: Record<string, unknown>, ctx: DiffCtx, acc: MutableAcc) {
  const op = opObject["@op"];
  if (typeof op !== "string") return;

  if (op === "Insert" || op === "Delete") {
    handleInsertDelete(opObject, acc);
  }

  const currentNodeId = ctx.currentNodeId;
  const currentField = ctx.currentField;
  if (!currentNodeId) return;

  if (currentField && CHILD_SET_FIELDS.has(currentField)) {
    handleChildSetOperation(opObject, currentNodeId, acc);
    return;
  }

  if (op === "SwapValue" && currentField) {
    const before = opObject["@before"];
    const after = opObject["@after"];
    const nodeType = acc.nodeDiffs.get(currentNodeId)?.nodeType ?? "unknown";
    upsertNodeDiff(acc, currentNodeId, "modified", {
      changes: [{ field: currentField, oldValue: before, newValue: after }],
    });
    if (CONTENT_FIELDS.has(currentField) || nodeType === "code_content") {
      setContentDiff(
        acc,
        currentNodeId,
        toContentType(currentField, nodeType),
        before,
        after
      );
    }
    return;
  }

  if (op !== "KeepList") {
    upsertNodeDiff(acc, currentNodeId, "modified");
  }
}

function walkDiff(value: unknown, ctx: DiffCtx, acc: MutableAcc) {
  if (Array.isArray(value)) {
    for (const item of value) walkDiff(item, ctx, acc);
    return;
  }
  if (!isRecord(value)) return;

  const nextCtx: DiffCtx = {
    currentNodeId: typeof value["@id"] === "string" ? value["@id"] : ctx.currentNodeId,
    currentField: ctx.currentField,
  };

  if (typeof value["@op"] === "string") {
    handleOperation(value, nextCtx, acc);
  }
  if (value["@rest"] != null) {
    walkDiff(value["@rest"], nextCtx, acc);
  }

  for (const [key, nested] of Object.entries(value)) {
    if (key.startsWith("@")) continue;
    walkDiff(nested, { ...nextCtx, currentField: key }, acc);
  }
}

export function parseVersioningDiff(
  diff: TerminusJsonDiff | undefined,
  commitBefore: string,
  commitAfter: string
): DiffResult {
  const acc: MutableAcc = {
    nodeDiffs: new Map(),
    contentDiffs: new Map(),
    relationshipAddedSet: new Set(),
    relationshipRemovedSet: new Set(),
    relationshipChanges: { added: [], removed: [] },
  };

  if (diff) {
    walkDiff(diff, { currentNodeId: null, currentField: null }, acc);
  }

  return {
    commitBefore,
    commitAfter,
    nodeDiffs: [...acc.nodeDiffs.values()],
    contentDiffs: [...acc.contentDiffs.values()],
    relationshipChanges: acc.relationshipChanges,
  };
}

