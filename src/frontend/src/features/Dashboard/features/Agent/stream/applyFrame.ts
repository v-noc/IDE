import { applyOperation } from "fast-json-patch";
import type { Operation } from "fast-json-patch";
import type { PatchOp, WireFrame } from "./types";
import { parseWireFrame } from "./types";

export type MirrorStatus = "open" | "closed" | "error";

export interface MirrorEntry {
  snapshot: unknown;
  lastSeq: number;
  status: MirrorStatus;
  error?: string;
}

function decodePointerToken(token: string): string {
  return token.replace(/~1/g, "/").replace(/~0/g, "~");
}

function getByPointer(data: unknown, path: string): unknown {
  if (!path || path === "/") return data;
  let current: unknown = data;
  for (const raw of path.replace(/^\//, "").split("/")) {
    const token = decodePointerToken(raw);
    if (current == null || typeof current !== "object") {
      throw new Error(`Cannot resolve path ${path}`);
    }
    if (Array.isArray(current)) {
      current = current[Number(token)];
    } else {
      current = (current as Record<string, unknown>)[token];
    }
  }
  return current;
}

function setByPointer(data: unknown, path: string, value: unknown): void {
  const tokens = path.replace(/^\//, "").split("/").map(decodePointerToken);
  let current: unknown = data;
  for (let i = 0; i < tokens.length - 1; i++) {
    const token = tokens[i]!;
    if (current == null || typeof current !== "object") {
      throw new Error(`Cannot resolve path ${path}`);
    }
    if (Array.isArray(current)) {
      current = current[Number(token)];
    } else {
      current = (current as Record<string, unknown>)[token];
    }
  }
  const last = tokens[tokens.length - 1]!;
  if (current == null || typeof current !== "object") {
    throw new Error(`Cannot set path ${path}`);
  }
  if (Array.isArray(current)) {
    current[Number(last)] = value;
  } else {
    (current as Record<string, unknown>)[last] = value;
  }
}

/**
 * Apply ops with `append` pre-pass, then standard JSON Patch.
 * Clones the whole snapshot (fine for F1; path-local clone is a later seam).
 */
export function applyOps(snapshot: unknown, ops: PatchOp[]): unknown {
  const result = structuredClone(snapshot);
  const standard: Operation[] = [];

  for (const op of ops) {
    if (op.op === "append") {
      const existing = getByPointer(result, op.path);
      if (typeof existing !== "string") {
        throw new TypeError(`append target at ${op.path} is not a string`);
      }
      setByPointer(result, op.path, existing + String(op.value));
    } else {
      standard.push(op as Operation);
    }
  }

  for (const op of standard) {
    applyOperation(result as object, op, false, true);
  }

  return result;
}

export function applyFrame(
  frame: WireFrame,
  docs: Record<string, MirrorEntry>,
): Record<string, MirrorEntry> {
  switch (frame.kind) {
    case "open":
      return {
        ...docs,
        [frame.doc]: {
          snapshot: structuredClone(frame.snapshot),
          lastSeq: -1,
          status: "open",
        },
      };

    case "patch": {
      const current = docs[frame.doc];
      if (!current) {
        console.warn(`[agent] patch before open for ${frame.doc}`);
        return docs;
      }
      if (frame.seq <= current.lastSeq) {
        console.warn(
          `[agent] stale patch seq=${frame.seq}, last=${current.lastSeq}`,
        );
        return docs;
      }
      if (frame.seq > current.lastSeq + 1) {
        console.warn(
          `[agent] patch gap: expected ${current.lastSeq + 1}, got ${frame.seq}`,
        );
      }
      return {
        ...docs,
        [frame.doc]: {
          ...current,
          snapshot: applyOps(current.snapshot, frame.ops),
          lastSeq: frame.seq,
          status: "open",
        },
      };
    }

    case "close": {
      const current = docs[frame.doc];
      if (!current) {
        return {
          ...docs,
          [frame.doc]: {
            snapshot: null,
            lastSeq: -1,
            status: frame.status === "error" ? "error" : "closed",
            error: frame.message ?? undefined,
          },
        };
      }
      return {
        ...docs,
        [frame.doc]: {
          ...current,
          status: frame.status === "error" ? "error" : "closed",
          error: frame.message ?? undefined,
        },
      };
    }
  }
}

export function parseAndApplyFrame(
  raw: unknown,
  docs: Record<string, MirrorEntry>,
): Record<string, MirrorEntry> | null {
  const frame = parseWireFrame(raw);
  if (!frame) return null;
  return applyFrame(frame, docs);
}
