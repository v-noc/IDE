import useProjectStore from "@/stores/useProjectStore";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";

export const useTreeNode = (node: ProjectTreeResponse) => {
  const {
    selectedNode,
    setSelectedNode,
    activeNodeId,
    expandedNodeIds,
    toggleNodeExpansion,
  } = useProjectStore();

  const isOpen = expandedNodeIds.has(node.key);
  const isSelected = selectedNode?.key === node.key;
  const isActive = activeNodeId === node.key;
  const hasChildren = node.children && node.children.length > 0;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node.key);
  };

  const handleSelectNode = () => {
    setSelectedNode(node);
  };

  const handleFocus = () => {
    console.log("Focus on:", node.name);
  };

  const handleExpand = () => {
    console.log("Expand:", node.name);
    if (hasChildren) {
      toggleNodeExpansion(node.key);
    }
  };

  const handleRemove = () => {
    console.log("Remove:", node.name);
  };

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
  };
};
