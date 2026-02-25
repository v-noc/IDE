import type { DiffStatus } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import type { TerminusJsonDiff } from "@/services/versioning";

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

export interface ParentChildDiff {
  added: string[];
  removed: string[];
}

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

function toIdList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string");
  }
  if (typeof value === "string") {
    return [value];
  }
  return [];
}

function extractSwapListOps(operation: Record<string, unknown>): {
  before: string[];
  after: string[];
}[] {
  const op = operation["@op"];
  const result: { before: string[]; after: string[] }[] = [];
  if (op === "SwapList") {
    result.push({
      before: toIdList(operation["@before"]),
      after: toIdList(operation["@after"]),
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
            before: toIdList(patchItem["@before"]),
            after: toIdList(patchItem["@after"]),
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
  added: string[],
  removed: string[]
) {
  if (!added.length && !removed.length) return;

  const current = parentChildDiffs[parentId] ?? { added: [], removed: [] };
  const addedSet = new Set(current.added);
  const removedSet = new Set(current.removed);

  for (const id of added) {
    addedSet.add(id);
  }
  for (const id of removed) {
    removedSet.add(id);
  }

  parentChildDiffs[parentId] = {
    added: [...addedSet],
    removed: [...removedSet],
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
    const before = toIdList(opObject["@before"]);
    const after = toIdList(opObject["@after"]);

    const swapListOps = extractSwapListOps(opObject);
    for (const swap of swapListOps) {
      before.push(...swap.before);
      after.push(...swap.after);
    }

    const beforeSet = new Set(before);
    const afterSet = new Set(after);

    const removed = [...beforeSet].filter((id) => !afterSet.has(id));
    const added = [...afterSet].filter((id) => !beforeSet.has(id));

    // The parent document changed because its child-set membership changed.
    addNodeDiff(nodeDiffs, currentDocId, "updated");
    addParentChildDiff(parentChildDiffs, currentDocId, added, removed);
    for (const id of added) {
      addNodeDiff(nodeDiffs, id, "added");
    }
    for (const id of removed) {
      addNodeDiff(nodeDiffs, id, "removed");
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
