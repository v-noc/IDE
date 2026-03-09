import type { AnyNodeTree, ProjectNodeTree, NodeType } from "@/types/project";
import type { DiffResult, DiffType } from "../types/diff";

function buildStatusMap(diffResult: DiffResult | null): Map<string, DiffType> {
  const map = new Map<string, DiffType>();
  if (!diffResult) return map;

  for (const nodeDiff of diffResult.nodeDiffs) {
    map.set(nodeDiff.nodeId, nodeDiff.status);
  }
  return map;
}

function mapDiffNodeTypeToTreeNodeType(type: string): NodeType {
  if (type === "project") return "project";
  if (type === "folder") return "folder";
  if (type === "file") return "file";
  if (type === "function") return "function";
  if (type === "class") return "class";
  if (type === "call") return "call";
  if (type === "group") return "group";
  return "container";
}

function nodeTypeFromBody(body: Record<string, unknown>, fallback: NodeType): NodeType {
  const nodeType = body.node_type;
  if (
    nodeType === "project" ||
    nodeType === "folder" ||
    nodeType === "file" ||
    nodeType === "function" ||
    nodeType === "class" ||
    nodeType === "call" ||
    nodeType === "group" ||
    nodeType === "container"
  ) {
    return nodeType;
  }
  return fallback;
}

function toAnyNodeTree(
  nodeId: string,
  status: DiffType,
  fallbackType: NodeType,
  body?: Record<string, unknown>,
): AnyNodeTree {
  const now = new Date(0).toISOString();
  const source = body ?? {};
  const name =
    typeof source.name === "string" && source.name.trim().length > 0
      ? source.name
      : nodeId.split("/").pop() ?? nodeId;

  return {
    id: nodeId,
    name,
    description: typeof source.description === "string" ? source.description : "",
    created_at: typeof source.created_at === "string" ? source.created_at : now,
    updated_at: typeof source.updated_at === "string" ? source.updated_at : now,
    node_type: nodeTypeFromBody(source, fallbackType),
    diff_status: status,
    children: [],
  } as unknown as AnyNodeTree;
}

function appendMissingRemovedNodes(
  tree: ProjectNodeTree,
  diffResult: DiffResult | null,
  statusMap: Map<string, DiffType>,
): ProjectNodeTree {
  if (!diffResult) return tree;

  const nodeMap = new Map<string, AnyNodeTree>();
  const walk = (node: AnyNodeTree) => {
    nodeMap.set(node.id, node);
    (node.children ?? []).forEach((child) => walk(child as AnyNodeTree));
  };
  walk(tree);

  for (const rel of diffResult.relationshipChanges.removed) {
    if (nodeMap.has(rel.child)) continue;
    const parent = nodeMap.get(rel.parent);
    if (!parent || !Array.isArray(parent.children)) continue;

    const removedDiff = diffResult.nodeDiffs.find((n) => n.nodeId === rel.child);
    const fallbackType = mapDiffNodeTypeToTreeNodeType(removedDiff?.nodeType ?? "unknown");
    const status = statusMap.get(rel.child) ?? "removed";
    const injected = toAnyNodeTree(rel.child, status, fallbackType, removedDiff?.before);
    const parentChildren = parent.children as AnyNodeTree[];
    (parent as unknown as { children: AnyNodeTree[] }).children = [
      ...parentChildren,
      injected,
    ];
    nodeMap.set(rel.child, injected);
  }

  return tree;
}

function annotateNode(
  node: AnyNodeTree,
  statusMap: Map<string, DiffType>,
): AnyNodeTree {
  const children = (node.children ?? []) as AnyNodeTree[];
  return {
    ...node,
    diff_status: statusMap.get(node.id) ?? "none",
    children: children.map((child) => annotateNode(child, statusMap)),
  } as AnyNodeTree;
}

export function applyNodeDiffStatus(
  projectTree: ProjectNodeTree | null,
  diffResult: DiffResult | null,
): ProjectNodeTree | null {
  if (!projectTree) return null;
  const statusMap = buildStatusMap(diffResult);
  const annotated = annotateNode(projectTree, statusMap) as ProjectNodeTree;
  return appendMissingRemovedNodes(annotated, diffResult, statusMap);
}
