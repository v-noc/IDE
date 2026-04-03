import { useMemo } from "react";
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
import { mergeStructureAndLazyChildren } from "@/features/Dashboard/utils/mergeCodeTreeChildren";

const EMPTY_METADATA_MAP = new Map<string, NodeMetadata>();

// Constants for card size - Adjust these to match your actual CSS node size!
const NODE_WIDTH = 350;
const NODE_HEIGHT = 150;

interface UseEnhancedTreeLayoutProps {
  centerNode: SimpleTreeNode | null;
  expandedNodeIds: string[];
  selectedNode?: SimpleTreeNode;
  toggleNodeExpansion: (nodeId: string) => void;
  nodeMetadataMap?: Map<string, NodeMetadata>;
  layoutConfig?: Partial<typeof LAYOUT_CONFIG>;
  /** Lazy-loaded `/descendants` roots keyed by parent id (same cache as sidebar). */
  lazyChildrenByParentId?: ReadonlyMap<string, AnyNodeTree[]>;
}

export const useEnhancedTreeLayout = ({
  centerNode,

  expandedNodeIds,
  toggleNodeExpansion,
  nodeMetadataMap,
  layoutConfig: _layoutConfig,
  lazyChildrenByParentId,
}: UseEnhancedTreeLayoutProps) => {
  const metadataMap = nodeMetadataMap ?? EMPTY_METADATA_MAP;

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
    const visitedNodeIds = new Set<string>();

    const expandedSet = new Set(expandedNodeIds);
    /**
     * Empty expansion list: show full subtree (first paint / no sidebar toggles yet).
     * After any id is tracked, only those nodes render their children—CanvasView expands
     * the path to the focused node so the center subtree stays reachable.
     */
    const expansionBootstrapped = expandedNodeIds.length > 0;

    const isExpanded = (nodeId: string) =>
      !expansionBootstrapped || expandedSet.has(nodeId);

    const canExpand = (node: SimpleTreeNode) =>
      (node.children?.length ?? 0) > 0 ||
      (node.lazy_child_ids?.length ?? 0) > 0;

    const mergeMetadata = (node: SimpleTreeNode): NodeMetadata | undefined => {
      const mapped = metadataMap.get(node.id);
      return {
        ...mapped,
        ...(node.metadata ?? {}),
        createdAt: node.created_at,
        updatedAt: node.updated_at,
        description: node.target ? node.target?.description : node.description,
      };
    };

    // 2. Recursive Traversal to build the Graph Data (Nodes/Edges)
    const traverse = (node: SimpleTreeNode) => {
      const nodeId = node.id;
      if (visitedNodeIds.has(nodeId)) {
        return;
      }
      visitedNodeIds.add(nodeId);

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
            <DynamicIcon
              iconName={getIcons(
                node.target ? node.target.node_type : node.node_type,
              )}
            />
          ),
          cornerIcon: getIcons(node.node_type),
          bgColor: nodeStyle.cardColor ?? nodeStyle.backgroundColor ?? "white",
          textColor: nodeStyle.textColor,
          iconColor: nodeStyle.iconColor,
          borderColor: nodeStyle.borderColor,
          expandable: canExpand(node),
          expanded: isExpanded(nodeId),
          onToggle: () => toggleNodeExpansion(nodeId),
          metadata: mergeMetadata(node),
          nodeType: node.node_type,
          nodeId: nodeId,
          target: node.target,

          manuallyCreated:
            (node as unknown as { manually_created?: boolean })
              .manually_created ?? false,
          diffStatus: (node as unknown as { status?: string }).status ?? null,
        } as EnhancedNodeData,
        type: "enhanced",
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };

      nodes.push(rfNode);

      // Tell Dagre about this node and its dimensions
      dagreGraph.setNode(nodeId, { width: NODE_WIDTH, height: NODE_HEIGHT });

      // Process Children if expanded
      if (isExpanded(nodeId)) {
        const lazyExtra = lazyChildrenByParentId?.get(nodeId);
        const childrenToRender = mergeStructureAndLazyChildren(
          node.children,
          lazyExtra,
        );

        if (childrenToRender.length === 0) {
          return;
        }

        childrenToRender.forEach((child: AnyNodeTree) => {
          const simpleChild = child as unknown as SimpleTreeNode;
          const childId = simpleChild.id;

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
          if (!visitedNodeIds.has(childId)) {
            traverse(simpleChild);
          }
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
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target),
    );

    return { initialNodes: layoutedNodes, initialEdges: validEdges };
    // DO not add toggleNodeExpansion to the dependency array
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [centerNode, expandedNodeIds, metadataMap]);
  return { initialNodes, initialEdges };
};
