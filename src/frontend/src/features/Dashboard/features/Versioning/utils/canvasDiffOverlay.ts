import React from "react";
import { Position, type Edge, type Node } from "@xyflow/react";
import { DynamicIcon } from "@/components/DynamicIcon";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
import getIcons from "@/features/Dashboard/utils/getIcons";
import getNodeStyle from "@/features/Dashboard/utils/getNodeStyle";
import type {
  AnyNodeTree,
  ContainerNodeTree,
  NodeType,
  ProjectNodeTree,
} from "@/types/project";
import type {
  OverlayDiffNodeRef,
  OverlayParentChildDiff,
} from "../store/useVersioningStore";
import type { DiffType } from "../types/diff";

function extractSchemaTypeName(raw: string): string {
  const compact = raw.trim();
  const slashToken = compact.split("/").pop() ?? compact;
  const hashToken = slashToken.split("#").pop() ?? slashToken;
  const colonToken = hashToken.split(":").pop() ?? hashToken;
  return colonToken.toLowerCase();
}

function toFrontendNodeType(typeValue: unknown): NodeType | null {
  if (typeof typeValue !== "string" || typeValue.trim() === "") return null;
  const normalized = extractSchemaTypeName(typeValue);
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

type OverlayNodesResult = {
  nodes: Node[];
  nodeIds: Set<string>;
};

const VALID_NODE_TYPES: Set<NodeType> = new Set([
  "container",
  "function",
  "class",
  "call",
  "file",
  "folder",
  "project",
  "group",
]);

function withDiffStatus(node: Node, nodeDiffs: Record<string, DiffType>): Node {
  return {
    ...node,
    data: {
      ...(node.data as Record<string, unknown>),
      diffStatus: nodeDiffs[node.id] ?? null,
    },
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function asNodeType(value: unknown, fallback: NodeType = "file"): NodeType {
  if (typeof value === "string" && VALID_NODE_TYPES.has(value as NodeType)) {
    return value as NodeType;
  }
  return fallback;
}

export type FallbackNodeData = {
  id: string;
  name: string;
  node_type: NodeType;
  icon?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  manually_created?: boolean;
  target?: { id: string; node_type: NodeType; description?: string };
};

function fromProjectNode(node: AnyNodeTree): FallbackNodeData {
  const targetRecord = asRecord((node as { target?: unknown }).target);
  const targetId = targetRecord && typeof targetRecord.id === "string"
    ? targetRecord.id
    : null;


  return {
    id: node.id,
    name: node.name || node.id,
    node_type: asNodeType(node.node_type, "file"),
    icon: typeof (node as { icon?: unknown }).icon === "string"
      ? ((node as { icon?: string }).icon)
      : undefined,
    description: typeof (node as { description?: unknown }).description === "string"
      ? ((node as { description?: string }).description)
      : undefined,
    created_at: node.created_at,
    updated_at: node.updated_at,
    manually_created: Boolean((node as { manually_created?: unknown }).manually_created),
    target: targetId
      ? {
        id: targetId,
        node_type: asNodeType(targetRecord?.node_type, "function"),
        description:
          typeof targetRecord?.description === "string"
            ? targetRecord.description
            : undefined,
      }
      : undefined,
  };
}

function fromDiffBody(
  ref: OverlayDiffNodeRef
): FallbackNodeData | null {
  let body = asRecord(ref.body);
  if (!body) return null;

  const id =
    typeof body["@id"] === "string"
      ? body["@id"]
      : typeof body.id === "string"
        ? body.id
        : ref.id;

  const targetRecord = asRecord(body.target);
  const targetId = targetRecord && typeof targetRecord.id === "string"
    ? targetRecord.id
    : null;



  const fallbackType = (body.node_type ?? toFrontendNodeType(body["@type"])) || "file";

  return {
    id,
    name: typeof body.name === "string" ? body.name : id,
    node_type: asNodeType(fallbackType, "file"),
    icon: typeof body.icon === "string" ? body.icon : undefined,
    description: typeof body.description === "string" ? body.description : undefined,
    created_at: typeof body.created_at === "string" ? body.created_at : undefined,
    updated_at: typeof body.updated_at === "string" ? body.updated_at : undefined,
    manually_created: Boolean(body.manually_created),
    target: targetId
      ? {
        id: targetId,
        node_type: asNodeType(targetRecord?.node_type, "function"),
        description:
          typeof targetRecord?.description === "string"
            ? targetRecord.description
            : undefined,
      }
      : undefined,
  };
}

export function createFallbackNode(
  childRef: OverlayDiffNodeRef,
  parentId: string,
  parentNode: Node | undefined,
  projectData: ProjectNodeTree | null | undefined,
  index: number
): Node | null {
  const fromStore = projectData ? findNodeByKey(projectData, childRef.id) : null;
  const source = fromStore ? fromProjectNode(fromStore) : fromDiffBody(childRef);
  if (!source) return null;

  const nodeStyle = getNodeStyle(source as unknown as ContainerNodeTree);
  const x = (parentNode?.position.x ?? 0) + 430;
  const y = (parentNode?.position.y ?? 0) + index * 180;
  const iconName =
    source.icon ??
    getIcons(source.target?.node_type ? source.target.node_type : source.node_type);

  return {
    id: source.id,
    position: { x, y },
    type: "enhanced",
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    data: {
      name: source.name || source.id,
      mainIcon: React.createElement(DynamicIcon, { iconName }),
      cornerIcon: getIcons(source.node_type),
      bgColor: nodeStyle.cardColor ?? nodeStyle.backgroundColor ?? "white",
      textColor: nodeStyle.textColor ?? "#1C1B1F",
      iconColor: nodeStyle.iconColor ?? "#49454F",
      borderColor: nodeStyle.borderColor ?? "#E7E0EC",
      expandable: false,
      expanded: true,
      metadata: {
        description: source.target?.description ?? source.description,
        createdAt: source.created_at,
        updatedAt: source.updated_at,
      },
      nodeType: source.node_type,
      nodeId: source.id,
      target: source.target,
      manuallyCreated: source.manually_created ?? false,
      parentId,
      isInjected: true,
    },
  };
}

export function buildDiffOverlayNodes(
  initialNodes: Node[],
  currentNodes: Node[],
  parentChildDiffs: Record<string, OverlayParentChildDiff>,
  nodeDiffs: Record<string, DiffType>,
  projectData?: ProjectNodeTree | null
): OverlayNodesResult {
  const currentNodeMap = new Map(currentNodes.map((n) => [n.id, n]));

  const mergedNodes = initialNodes.map((newNode) => {
    const existingNode = currentNodeMap.get(newNode.id);
    if (existingNode) {
      return withDiffStatus(
        {
          ...existingNode,
          position: newNode.position,
          data: {
            ...(existingNode.data as Record<string, unknown>),
            ...(newNode.data as Record<string, unknown>),
          },
        },
        nodeDiffs
      );
    }
    return withDiffStatus(newNode, nodeDiffs);
  });

  if (Object.keys(parentChildDiffs).length === 0) {
    return { nodes: mergedNodes, nodeIds: new Set(mergedNodes.map((n) => n.id)) };
  }

  const mergedNodeMap = new Map(mergedNodes.map((n) => [n.id, n]));
  const injectedPerParent = new Map<string, number>();
  for (const [parentId, diff] of Object.entries(parentChildDiffs)) {
    const parentNode = mergedNodeMap.get(parentId);
    if (!parentNode) {
      continue;
    }
    const parentData = (parentNode.data ?? {}) as Record<string, unknown>;
    const isParentExpanded =
      parentData.expandable === false || Boolean(parentData.expanded);
    if (!isParentExpanded) {
      continue;
    }

    const childRefs = [...diff.added, ...diff.removed];
    for (const childRef of childRefs) {
      const childId = childRef.id;
      if (mergedNodeMap.has(childId)) continue;
      const existingNode = currentNodeMap.get(childId);
      if (existingNode) {
        mergedNodeMap.set(childId, withDiffStatus(existingNode, nodeDiffs));
        continue;
      }
      const injectionIndex = injectedPerParent.get(parentId) ?? 0;
      const fallbackNode = createFallbackNode(
        childRef,
        parentId,
        parentNode,
        projectData,
        injectionIndex
      );
      if (!fallbackNode) continue;
      mergedNodeMap.set(childId, withDiffStatus(fallbackNode, nodeDiffs));
      injectedPerParent.set(parentId, injectionIndex + 1);
    }
  }

  const nodes = [...mergedNodeMap.values()];
  return { nodes, nodeIds: new Set(nodes.map((n) => n.id)) };
}

export function buildDiffOverlayEdges(
  initialEdges: Edge[],
  parentChildDiffs: Record<string, OverlayParentChildDiff>,
  nodeIds: Set<string>
): Edge[] {
  if (Object.keys(parentChildDiffs).length === 0) {
    return initialEdges;
  }

  const edgeMap = new Map(initialEdges.map((edge) => [edge.id, edge]));
  for (const [parentId, diff] of Object.entries(parentChildDiffs)) {
    const childRefs = [...diff.added, ...diff.removed];
    for (const childRef of childRefs) {
      const childId = childRef.id;
      if (!nodeIds.has(parentId) || !nodeIds.has(childId)) continue;
      const edgeId = `${parentId}-${childId}`;
      if (edgeMap.has(edgeId)) continue;
      edgeMap.set(edgeId, {
        id: edgeId,
        source: parentId,
        target: childId,
        type: "bezier",
      });
    }
  }

  return [...edgeMap.values()];
}
