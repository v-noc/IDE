import type {
  DiffNodeRef,
  DiffStatus,
  ParentChildDiff,
} from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import type { TerminusJsonDiff } from "@/services/versioning";
import type { NodeType } from "@/types/project";

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

export interface CanvasDiffResult {
  nodeDiffs: Record<string, DiffStatus>;
  parentChildDiffs: Record<string, ParentChildDiff>;
}

type DiffCtx = {
  currentDocumentId: string | null;
  currentField: string | null;
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
  return colonToken;
}

function toFrontendNodeType(typeValue: unknown): NodeType | null {
  if (typeof typeValue !== "string" || typeValue.trim() === "") {
    return null;
  }
  const normalized = extractSchemaTypeName(typeValue).toLowerCase();
  if (normalized.includes("project")) return "project";
  if (normalized.includes("folder")) return "folder";
  if (normalized.includes("file")) return "file";
  if (normalized.includes("function")) return "function";
  if (normalized.includes("class")) return "class";
  if (normalized.includes("codeelementgroup")) return "group";
  if (normalized.includes("structuregroup")) return "group";
  if (normalized.includes("callgroup")) return "group";
  if (normalized.includes("group")) return "group";
  if (normalized.includes("call")) return "call";
  return null;
}

function normalizeTarget(value: unknown): Record<string, unknown> | undefined {
  if (!isRecord(value)) return undefined;
  const id = readId(value);
  if (!id) return undefined;

  const targetNodeType =
    (typeof value.node_type === "string" && (value.node_type as NodeType)) ||
    toFrontendNodeType(value["@type"]) ||
    "function";

  return {
    ...value,
    id,
    node_type: targetNodeType,
  };
}

function normalizeDiffNodeBody(value: Record<string, unknown>): Record<string, unknown> {
  const id = readId(value);
  const nodeType =
    (typeof value.node_type === "string" && (value.node_type as NodeType)) ||
    toFrontendNodeType(value["@type"]);
  const target =
    normalizeTarget(value.target) ?? normalizeTarget(value.target_function);

  return {
    ...value,
    ...(id ? { id, "@id": id } : {}),
    ...(nodeType ? { node_type: nodeType } : {}),
    ...(target ? { target } : {}),
  };
}

function toNodeRef(value: unknown): DiffNodeRef | null {
  if (typeof value === "string") {
    return { id: value };
  }
  if (!isRecord(value)) {
    return null;
  }

  const normalized = normalizeDiffNodeBody(value);
  const id = readId(normalized);
  if (!id) {
    return null;
  }
  return { id, body: normalized };
}

function mergeNodeRefs(existing: DiffNodeRef[], next: DiffNodeRef[]): DiffNodeRef[] {
  const merged = new Map(existing.map((entry) => [entry.id, entry]));
  for (const entry of next) {
    const current = merged.get(entry.id);
    if (!current || (!current.body && entry.body)) {
      merged.set(entry.id, entry);
    }
  }
  return [...merged.values()];
}

function toNodeRefList(value: unknown): DiffNodeRef[] {
  if (Array.isArray(value)) {
    const refs = value
      .map((item) => toNodeRef(item))
      .filter((item): item is DiffNodeRef => item !== null);
    return mergeNodeRefs([], refs);
  }
  const ref = toNodeRef(value);
  return ref ? [ref] : [];
}

function extractSwapListOps(operation: Record<string, unknown>): {
  before: DiffNodeRef[];
  after: DiffNodeRef[];
}[] {
  const op = operation["@op"];
  const result: { before: DiffNodeRef[]; after: DiffNodeRef[] }[] = [];
  if (op === "SwapList") {
    result.push({
      before: toNodeRefList(operation["@before"]),
      after: toNodeRefList(operation["@after"]),
    });
    const rest = operation["@rest"];
    if (isRecord(rest)) {
      result.push(...extractSwapListOps(rest));
    }
    return result;
  }

  if (op === "PatchList") {
    const patchItems = operation["@patch"];
    if (Array.isArray(patchItems)) {
      for (const patchItem of patchItems) {
        if (!isRecord(patchItem)) continue;
        if (patchItem["@op"] === "SwapValue") {
          result.push({
            before: toNodeRefList(patchItem["@before"]),
            after: toNodeRefList(patchItem["@after"]),
          });
        }
      }
    }
    const rest = operation["@rest"];
    if (isRecord(rest)) {
      result.push(...extractSwapListOps(rest));
    }
    return result;
  }

  if (op === "CopyList") {
    const rest = operation["@rest"];
    if (isRecord(rest)) {
      result.push(...extractSwapListOps(rest));
    }
  }
  return result;
}

function mergeDiffStatus(
  current: DiffStatus,
  next: Exclude<DiffStatus, null>
): Exclude<DiffStatus, null> {
  if (!current) return next;
  if (current === next) return current;
  if (current === "updated") return "updated";
  if (next === "updated") return "updated";
  // added + removed (or reverse) usually means move/change between sets.
  return "updated";
}

function addNodeDiff(
  nodeDiffs: Record<string, DiffStatus>,
  nodeId: string,
  status: Exclude<DiffStatus, null>
) {
  nodeDiffs[nodeId] = mergeDiffStatus(nodeDiffs[nodeId] ?? null, status);
}

function addParentChildDiff(
  parentChildDiffs: Record<string, ParentChildDiff>,
  parentId: string,
  added: DiffNodeRef[],
  removed: DiffNodeRef[]
) {
  if (!added.length && !removed.length) return;

  const current = parentChildDiffs[parentId] ?? { added: [], removed: [] };

  parentChildDiffs[parentId] = {
    added: mergeNodeRefs(current.added, added),
    removed: mergeNodeRefs(current.removed, removed),
  };
}

function handleOperation(
  opObject: Record<string, unknown>,
  ctx: DiffCtx,
  nodeDiffs: Record<string, DiffStatus>,
  parentChildDiffs: Record<string, ParentChildDiff>
) {
  const op = opObject["@op"];
  if (typeof op !== "string") return;

  const currentDocId = ctx.currentDocumentId;
  const currentField = ctx.currentField;
  const isChildSetOperation = !!(
    currentDocId &&
    currentField &&
    CHILD_SET_FIELDS.has(currentField)
  );

  if (isChildSetOperation) {
    let before = toNodeRefList(opObject["@before"]);
    let after = toNodeRefList(opObject["@after"]);

    const swapListOps = extractSwapListOps(opObject);
    for (const swap of swapListOps) {
      before = mergeNodeRefs(before, swap.before);
      after = mergeNodeRefs(after, swap.after);
    }

    const beforeMap = new Map(before.map((entry) => [entry.id, entry]));
    const afterMap = new Map(after.map((entry) => [entry.id, entry]));

    const removed = [...beforeMap.keys()]
      .filter((id) => !afterMap.has(id))
      .map((id) => beforeMap.get(id))
      .filter((entry): entry is DiffNodeRef => !!entry);
    const added = [...afterMap.keys()]
      .filter((id) => !beforeMap.has(id))
      .map((id) => afterMap.get(id))
      .filter((entry): entry is DiffNodeRef => !!entry);

    // The parent document changed because its child-set membership changed.
    addNodeDiff(nodeDiffs, currentDocId, "updated");
    addParentChildDiff(parentChildDiffs, currentDocId, added, removed);
    for (const entry of added) {
      addNodeDiff(nodeDiffs, entry.id, "added");
    }
    for (const entry of removed) {
      addNodeDiff(nodeDiffs, entry.id, "removed");
    }
    return;
  }

  if (currentDocId && op !== "KeepList") {
    addNodeDiff(nodeDiffs, currentDocId, "updated");
  }
}

function walkDiff(
  value: unknown,
  ctx: DiffCtx,
  nodeDiffs: Record<string, DiffStatus>,
  parentChildDiffs: Record<string, ParentChildDiff>
) {
  if (Array.isArray(value)) {
    for (const item of value) {
      walkDiff(item, ctx, nodeDiffs, parentChildDiffs);
    }
    return;
  }

  if (!isRecord(value)) return;

  const nextCtx: DiffCtx = {
    currentDocumentId:
      typeof value["@id"] === "string" ? String(value["@id"]) : ctx.currentDocumentId,
    currentField: ctx.currentField,
  };

  if (typeof value["@op"] === "string") {
    handleOperation(value, nextCtx, nodeDiffs, parentChildDiffs);
  }

  for (const [key, nested] of Object.entries(value)) {
    if (key.startsWith("@")) continue;
    walkDiff(
      nested,
      { ...nextCtx, currentField: key },
      nodeDiffs,
      parentChildDiffs
    );
  }
}

export function parseTerminusJsonDiff(diff: TerminusJsonDiff | undefined): CanvasDiffResult {
  const nodeDiffs: Record<string, DiffStatus> = {};
  const parentChildDiffs: Record<string, ParentChildDiff> = {};

  if (!diff) {
    return { nodeDiffs, parentChildDiffs };
  }

  walkDiff(
    diff,
    { currentDocumentId: null, currentField: null },
    nodeDiffs,
    parentChildDiffs
  );

  return { nodeDiffs, parentChildDiffs };
}
