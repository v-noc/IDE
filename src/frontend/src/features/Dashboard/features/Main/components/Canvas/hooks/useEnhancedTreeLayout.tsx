import { useEffect, useMemo } from "react";
import type { Edge, Node } from "@xyflow/react";
import { Position } from "@xyflow/react";
import dagre from "dagre"; // Import dagre
import type { SimpleTreeNode } from "../components/nodeUtils";

import { LAYOUT_CONFIG } from "../components/layoutConfig"; // Assuming dimensions are here
import getNodeStyle from "@/features/Dashboard/utils/getNodeStyle";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import { DynamicIcon } from "@/components/DynamicIcon";
import type {
  EnhancedNodeData,
  NodeMetadata,
} from "../components/nodes/EnhancedNode";
import { getIcons } from "@/features/Dashboard/utils";

const EMPTY_METADATA_MAP = new Map<string, NodeMetadata>();

// Constants for card size - Adjust these to match your actual CSS node size!
const NODE_WIDTH = 350;
const NODE_HEIGHT = 150;

interface UseEnhancedTreeLayoutProps {
  centerNode: SimpleTreeNode | null;
  expandedNodeIds: string[];
  toggleNodeExpansion: (nodeId: string) => void;
  nodeMetadataMap?: Map<string, NodeMetadata>;
  layoutConfig?: Partial<typeof LAYOUT_CONFIG>;
  focusTargetId?: string | null;
}

export const useEnhancedTreeLayout = ({
  centerNode,
  expandedNodeIds,
  toggleNodeExpansion,
  nodeMetadataMap,
  layoutConfig: _layoutConfig,
  focusTargetId,
}: UseEnhancedTreeLayoutProps) => {
  const metadataMap = nodeMetadataMap ?? EMPTY_METADATA_MAP;
  console.log("focusTargetId", focusTargetId);
  // TODO: Use layoutConfig for dagre spacing configuration if needed
  void _layoutConfig;

  const { initialNodes, initialEdges } = useMemo(() => {
    if (!centerNode) {
      return { initialNodes: [], initialEdges: [] };
    }

    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // 1. Configure Layout Direction
    dagreGraph.setGraph({
      rankdir: "LR", // Left-to-Right
      align: "UL", // Align Up-Left
      nodesep: 100, // Vertical spacing between nodes
      ranksep: 200, // Horizontal spacing between ranks
    });

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Helper to check expansion
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

    // 2. Recursive Traversal to build the Graph Data (Nodes/Edges)
    const traverse = (node: SimpleTreeNode) => {
      const nodeId = node._key;

      // Prepare Node Data
      const nodeStyle = getNodeStyle(node as unknown as ContainerNodeTree);

      const rfNode: Node = {
        id: nodeId,
        // Initial position (will be overwritten by Dagre)
        position: { x: 0, y: 0 },
        data: {
          name: node.name,
          mainIcon: node.icon ? (
            <DynamicIcon iconName={node.icon} />
          ) : (
            <DynamicIcon iconName={getIcons(node.node_type)} />
          ),
          cornerIcon: getIcons(node.node_type),
          bgColor: nodeStyle.cardColor ?? nodeStyle.backgroundColor ?? "white",
          textColor: nodeStyle.textColor,
          iconColor: nodeStyle.iconColor,
          borderColor: nodeStyle.borderColor,
          expandable: (node.children?.length ?? 0) > 0,
          expanded: isExpanded(nodeId),
          onToggle: () => toggleNodeExpansion(nodeId),
          metadata: mergeMetadata(node),
          nodeType: node.node_type,
          nodeId: nodeId,
          target: node.target,
          focused: focusTargetId
            ? nodeId ===
              (focusTargetId.includes("/")
                ? focusTargetId.split("/").pop()
                : focusTargetId)
            : false,
          selected: nodeId === centerNode?._key,
        } as EnhancedNodeData,
        type: "enhanced",
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };

      nodes.push(rfNode);

      // Tell Dagre about this node and its dimensions
      dagreGraph.setNode(nodeId, { width: NODE_WIDTH, height: NODE_HEIGHT });

      // Process Children if expanded
      if (isExpanded(nodeId) && node.children && node.children.length > 0) {
        node.children.forEach((child: AnyNodeTree) => {
          const simpleChild = child as unknown as SimpleTreeNode;
          const childId = simpleChild._key;

          // Create Edge
          edges.push({
            id: `${nodeId}-${childId}`,
            source: nodeId,
            target: childId,
            type: "bezier", // 'smoothstep' looks better for trees than bezier
            animated: simpleChild.node_type === "call",
            style:
              simpleChild.node_type === "call"
                ? { stroke: "#3b82f6", strokeWidth: 2 }
                : undefined,
          });

          // Tell Dagre about the edge
          dagreGraph.setEdge(nodeId, childId);

          // Recurse
          traverse(simpleChild);
        });
      }
    };

    // Start traversal
    traverse(centerNode);

    // 3. Calculate Layout
    dagre.layout(dagreGraph);

    // 4. Apply calculated positions back to nodes
    const layoutedNodes = nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);

      // We need to shift the position because Dagre gives the center,
      // while React Flow expects the top-left corner
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - NODE_WIDTH / 2,
          y: nodeWithPosition.y - NODE_HEIGHT / 2,
        },
      };
    });

    // 5. Filter edges to only include those where both source and target nodes exist
    // This prevents "orphaned" edges when nodes are collapsed/removed
    const nodeIds = new Set(layoutedNodes.map((node) => node.id));
    const validEdges = edges.filter(
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    return { initialNodes: layoutedNodes, initialEdges: validEdges };
  }, [centerNode, expandedNodeIds, metadataMap, focusTargetId]);
  return { initialNodes, initialEdges };
};
