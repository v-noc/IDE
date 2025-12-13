import { useMemo } from "react";
import type { Edge, Node } from "@xyflow/react";
import { Position } from "@xyflow/react";
import type { SimpleTreeNode } from "../components/nodeUtils";
import { iconForType } from "../components/nodeUtils";
import { LAYOUT_CONFIG, calculateChildY } from "../components/layoutConfig";
import getNodeStyle from "@/features/Dashboard/utils/getNodeStyle";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import { DynamicIcon } from "@/components/DynamicIcon";
import type {
  EnhancedNodeData,
  NodeMetadata,
} from "../components/EnhancedNode";

const EMPTY_METADATA_MAP = new Map<string, NodeMetadata>();

interface UseEnhancedTreeLayoutProps {
  centerNode: SimpleTreeNode | null;
  expandedNodeIds: string[];
  toggleNodeExpansion: (nodeId: string) => void;
  nodeMetadataMap?: Map<string, NodeMetadata>;
  layoutConfig?: Partial<typeof LAYOUT_CONFIG>;
}

interface EnhancedTreeLayoutResult {
  initialNodes: Node[];
  initialEdges: Edge[];
}

/**
 * Enhanced version of useTreeLayout that supports rich node metadata
 * Includes created/updated dates, logs, warnings, errors, and code display
 */
export const useEnhancedTreeLayout = ({
  centerNode,
  expandedNodeIds,
  toggleNodeExpansion,
  nodeMetadataMap,
  layoutConfig,
}: UseEnhancedTreeLayoutProps): EnhancedTreeLayoutResult => {
  const metadataMap = nodeMetadataMap ?? EMPTY_METADATA_MAP;
  const config = useMemo(
    () => ({ ...LAYOUT_CONFIG, ...layoutConfig }),
    [layoutConfig]
  );

  return useMemo(() => {
    if (centerNode == null) {
      return { initialNodes: [], initialEdges: [] };
    }

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const isExpanded = (nodeId: string) =>
      expandedNodeIds.length === 0 || expandedNodeIds.includes(nodeId);

    const mergeMetadata = (node: SimpleTreeNode): NodeMetadata | undefined => {
      const mapped = metadataMap.get(node._key);
      return {
        ...mapped,
        ...(node.metadata ?? {}),
        createdAt: node.created_at,
        updatedAt: node.updated_at,
        description: node.description,
      };
    };

    const parentId = centerNode._key;
    const parentStyle = getNodeStyle(
      centerNode as unknown as ContainerNodeTree
    );

    nodes.push({
      id: parentId,
      position: { x: config.ROOT_X, y: config.ROOT_Y },
      data: {
        name: centerNode.name,
        mainIcon: centerNode.icon ? (
          <DynamicIcon iconName={centerNode.icon} />
        ) : (
          iconForType(centerNode.node_type)
        ),
        cornerIcon: iconForType(centerNode.node_type),
        bgColor: parentStyle.cardColor ?? "white",
        textColor: parentStyle.textColor,
        iconColor: parentStyle.iconColor,
        borderColor: parentStyle.borderColor,
        expandable: (centerNode.children?.length ?? 0) > 0,
        expanded: isExpanded(parentId),
        onToggle: () => toggleNodeExpansion(parentId),
        metadata: mergeMetadata(centerNode),
        nodeType: centerNode.node_type,
        nodeId: centerNode._key,
        target: centerNode.target,
      } as EnhancedNodeData,
      type: "enhanced",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    });

    const buildChildren = (
      parent: SimpleTreeNode,
      parentX: number,
      parentY: number
    ): void => {
      if (!isExpanded(parent._key)) return;

      const rawChildren: SimpleTreeNode[] = (parent.children ?? []).map(
        (child: AnyNodeTree) => child as unknown as SimpleTreeNode
      );
      if (rawChildren.length === 0) return;

      const nextLevelX = parentX + config.LEVEL_SPACING_X;

      rawChildren.forEach((child: SimpleTreeNode, index: number) => {
        const childId = child.target ? child.target._key : child._key;
        const childY =
          parentY +
          calculateChildY(index, rawChildren.length, config.SPACING_Y);

        const childStyle = getNodeStyle(child as unknown as ContainerNodeTree);

        nodes.push({
          id: childId,
          position: { x: nextLevelX, y: childY },
          data: {
            name: child.name,
            mainIcon: child.icon ? (
              <DynamicIcon iconName={child.icon} />
            ) : (
              iconForType(child.node_type)
            ),
            cornerIcon: iconForType(child.node_type),
            bgColor: childStyle.cardColor ?? childStyle.backgroundColor,
            textColor: childStyle.textColor,
            iconColor: childStyle.iconColor,
            borderColor: childStyle.borderColor,
            expandable: (child.children?.length ?? 0) > 0,
            expanded: isExpanded(childId),
            onToggle: () => toggleNodeExpansion(childId),
            metadata: mergeMetadata(child),
            nodeType: child.node_type,
            nodeId: childId,
            target: child.target,
          } as EnhancedNodeData,
          type: "enhanced",
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        });

        edges.push({
          id: `${parent._key}-${childId}`,
          source: parent.target ? parent.target._key : parent._key,
          target: childId,
          type: "smoothstep",
          animated: child.node_type === "call",
          style:
            child.node_type === "call"
              ? { stroke: "#3b82f6", strokeWidth: 2 }
              : undefined,
        });

        buildChildren(child, nextLevelX, childY);
      });
    };

    buildChildren(centerNode, config.ROOT_X, config.ROOT_Y);

    return { initialNodes: nodes, initialEdges: edges };
  }, [
    centerNode,
    config.LEVEL_SPACING_X,
    config.ROOT_X,
    config.ROOT_Y,
    config.SPACING_Y,
    expandedNodeIds,
    metadataMap,
    toggleNodeExpansion,
  ]);
};
