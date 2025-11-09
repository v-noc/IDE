import React, { useCallback, useMemo } from "react";
import {
  Background,
  Controls,
  type Edge,
  type FitViewOptions,
  type Node,
  Handle,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import { ChevronDown, ChevronRight } from "lucide-react";
import "@xyflow/react/dist/style.css";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import getNodeStyle from "@/features/Dashboard/utils/getNodeStyle";
import { DynamicIcon } from "@/components/DynamicIcon";

interface CanvasViewProps {
  projectId?: string;
}

const fitViewOptions: FitViewOptions = {
  padding: 0.2,
  minZoom: 0.2,
  maxZoom: 1.5,
};

type SimpleTreeNode = {
  _key: string;
  name: string;
  icon?: string;
  node_type: AnyNodeTree["node_type"];
  children?: AnyNodeTree[];
};

// removed inline label generator; custom node handles label rendering

const iconForType = (nodeType: AnyNodeTree["node_type"]) => {
  switch (nodeType) {
    case "project":
      return "📦";
    case "folder":
      return "📁";
    case "file":
      return "📄";
    case "class":
      return "🏷️";
    case "function":
      return "ƒ";
    case "call":
      return "🔗";
    case "group":
      return "🗂️";
    default:
      return "📌";
  }
};

type SimpleNodeData = {
  name: string;
  mainIcon: string;
  cornerIcon: string;
  bgColor: string;
  textColor: string;
  iconColor: string;
  borderColor: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
};

const SimpleNode: React.FC<{ data: SimpleNodeData }> = ({ data }) => {
  return (
    <div
      style={{
        position: "relative",
        background: data.bgColor,
        color: data.textColor,
        border: `1px solid ${data.borderColor}`,
        borderRadius: 14,
        padding: "12px 14px",
        minWidth: 160,
        boxShadow: "0 4px 12px rgba(0,0,0,0.10)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {data.expandable ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              data.onToggle?.();
            }}
            title={data.expanded ? "Collapse" : "Expand"}
            style={{
              width: 22,
              height: 22,
              borderRadius: 22,
              border: `1px solid ${data.borderColor}`,
              background: data.bgColor,
              color: data.iconColor,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 16,
              cursor: "pointer",
            }}
          >
            {data.expanded ? (
              <ChevronDown size={16} />
            ) : (
              <ChevronRight size={16} />
            )}
          </button>
        ) : null}
        <span style={{ fontSize: 18, color: data.iconColor }}>
          {data.mainIcon}
        </span>
        <span style={{ fontWeight: 600, letterSpacing: 0.2 }}>{data.name}</span>
      </div>

      {/* Floating circle badge */}
      <div
        style={{
          position: "absolute",
          top: -10,
          right: -10,
          width: 34,
          height: 34,
          borderRadius: "50%",
          background: data.bgColor,
          border: `1px solid ${data.borderColor}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 6px 14px rgba(0,0,0,0.15)",
        }}
      >
        <span style={{ fontSize: 16, color: data.iconColor }}>
          {data.cornerIcon}
        </span>
      </div>

      {/* Handles for edges */}
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
};

const CanvasView: React.FC<CanvasViewProps> = () => {
  const { selectedNode, expandedNodeIds, toggleNodeExpansion } =
    useProjectStore();

  const centerNode = selectedNode as SimpleTreeNode | null;

  const isExpanded = useMemo(() => {
    if (!centerNode) return false;
    return expandedNodeIds.includes(centerNode._key);
  }, [centerNode, expandedNodeIds]);

  const { initialNodes, initialEdges } = useMemo(() => {
    if (centerNode == null) {
      return { initialNodes: [], initialEdges: [] };
    }

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Parent in the center top
    const parentId = centerNode._key;
    const parentStyle = getNodeStyle(
      centerNode as unknown as ContainerNodeTree
    );
    nodes.push({
      id: parentId,
      position: { x: 0, y: 0 },
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
        expanded: expandedNodeIds.includes(parentId),
        onToggle: () => toggleNodeExpansion(parentId),
      },
      type: "simple",
      sourcePosition: Position.Bottom,
    });

    const SPACING_X = 220;
    const LEVEL_Y = 160;

    const buildChildren = (
      parent: SimpleTreeNode,
      parentX: number,
      depth: number
    ) => {
      if (!expandedNodeIds.includes(parent._key)) return;
      const rawChildren = (parent.children ?? []).map(
        (c) => c as unknown as SimpleTreeNode
      );
      if (rawChildren.length === 0) return;

      const startX = parentX - ((rawChildren.length - 1) * SPACING_X) / 2;
      const y = depth * LEVEL_Y;

      rawChildren.forEach((child, index) => {
        const id = child._key;
        const x = startX + index * SPACING_X;
        const s = getNodeStyle(child as unknown as ContainerNodeTree);
        nodes.push({
          id,
          position: { x, y },
          data: {
            name: child.name,
            mainIcon: child.icon ? (
              <DynamicIcon iconName={child.icon} />
            ) : (
              iconForType(child.node_type)
            ),
            cornerIcon: iconForType(child.node_type),
            bgColor: s.cardColor ?? s.backgroundColor,
            textColor: s.textColor,
            iconColor: s.iconColor,
            borderColor: s.borderColor,
            expandable: (child.children?.length ?? 0) > 0,
            expanded: expandedNodeIds.includes(id),
            onToggle: () => toggleNodeExpansion(id),
          },
          type: "simple",
          targetPosition: Position.Top,
          sourcePosition: Position.Bottom,
        });
        edges.push({
          id: `${parent._key}-${id}`,
          source: parent._key,
          target: id,
          type: "smoothstep",
        });

        if (expandedNodeIds.includes(child._key)) {
          buildChildren(child, x, depth + 1);
        }
      });
    };

    if (isExpanded) {
      buildChildren(centerNode, 0, 1);
    }

    return { initialNodes: nodes, initialEdges: edges };
  }, [centerNode, isExpanded, expandedNodeIds, toggleNodeExpansion]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state when center node changes
  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (!centerNode) return;
      // Toggle expansion for any clicked node in the subtree
      toggleNodeExpansion(node.id);
    },
    [centerNode, toggleNodeExpansion]
  );

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <ReactFlow
        nodeTypes={useMemo(() => ({ simple: SimpleNode }), [])}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={fitViewOptions}
      >
        <Background />
        <Controls position="bottom-right" />
      </ReactFlow>
    </div>
  );
};

export default CanvasView;
