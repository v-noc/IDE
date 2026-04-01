import type { AnyNodeTree, CodePosition, ContainerNodeTree } from "@/types/project";
import { schemaTypeToNodeType } from "./schemaToNodeType";

function pickString(raw: Record<string, unknown>, keys: string[]): string {
  for (const k of keys) {
    const v = raw[k];
    if (typeof v === "string" && v) return v;
  }
  return "";
}

function extractLazyIds(raw: Record<string, unknown>): string[] {
  const ch = raw.children;
  if (!Array.isArray(ch) || ch.length === 0) return [];
  if (typeof ch[0] === "string") return ch.filter((x): x is string => typeof x === "string");
  return [];
}

function pickPosition(raw: Record<string, unknown>): CodePosition {
  const cp = raw.code_position as Record<string, unknown> | undefined;
  if (cp && typeof cp === "object") {
    return {
      line_no: Number(cp.line_no ?? 0),
      col_offset: Number(cp.col_offset ?? 0),
      end_line_no:
        cp.end_line_no === null || cp.end_line_no === undefined
          ? null
          : Number(cp.end_line_no),
      end_col_offset:
        cp.end_col_offset === null || cp.end_col_offset === undefined
          ? null
          : Number(cp.end_col_offset),
    };
  }
  return {
    line_no: 0,
    col_offset: 0,
    end_line_no: null,
    end_col_offset: null,
  };
}

/**
 * Turn a /code-elements/descendants JSON object into a shallow tree node (nested children empty).
 */
export function normalizeCodeDescendant(raw: Record<string, unknown>): ContainerNodeTree {
  const id = pickString(raw, ["id", "@id"]);
  const schema = pickString(raw, ["type", "@type"]);
  const node_type = schemaTypeToNodeType(schema || "CodeElementGroupSchema");
  const lazy_child_ids = extractLazyIds(raw);

  const base = {
    id,
    name: pickString(raw, ["name"]) || id,
    description: pickString(raw, ["description"]),
    node_type,
    created_at: pickString(raw, ["created_at"]) || new Date(0).toISOString(),
    updated_at: pickString(raw, ["updated_at"]) || new Date(0).toISOString(),
    documents: [] as string[],
    children: [] as AnyNodeTree[],
    lazy_child_ids: lazy_child_ids.length ? lazy_child_ids : undefined,
    status: (raw.status as string) || "unchanged",
  };

  if (node_type === "group") {
    return {
      ...base,
      node_type: "group",
      group_type: schema.includes("CallGroup")
        ? "call_group"
        : "code_element_group",
    } as ContainerNodeTree;
  }

  if (node_type === "class") {
    return {
      ...base,
      node_type: "class",
      qname: pickString(raw, ["qname"]) || id,
      implements: [],
      position: pickPosition(raw),
    } as ContainerNodeTree;
  }

  if (node_type === "function") {
    return {
      ...base,
      node_type: "function",
      qname: pickString(raw, ["qname"]) || id,
      position: pickPosition(raw),
    } as ContainerNodeTree;
  }

  if (node_type === "call") {
    return {
      ...base,
      node_type: "call",
      position: pickPosition(raw),
      manually_created: Boolean(raw.manually_created),
    } as ContainerNodeTree;
  }

  return base as ContainerNodeTree;
}
