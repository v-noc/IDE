import useProjectStore from "@/stores/useProjectStore";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { useState } from "react";

export const useTreeNode = (node: ProjectTreeResponse) => {
  const {
    selectedNode,
    setSelectedNode,
    activeNodeId,
    expandedNodeIds,
    toggleNodeExpansion,
    addVirtualNode,
  } = useProjectStore();

  const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);
  const [nodeTypeToCreate, setNodeTypeToCreate] = useState<"file" | "folder">(
    "file"
  );

  const isOpen = expandedNodeIds.includes(node.key);
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

  const handleCreateFile = () => {
    setNodeTypeToCreate("file");
    setCreateDialogOpen(true);
  };

  const handleCreateFolder = () => {
    setNodeTypeToCreate("folder");
    setCreateDialogOpen(true);
  };

  const closeCreateDialog = () => {
    setCreateDialogOpen(false);
  };

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
    isCreateDialogOpen,
    nodeTypeToCreate,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
    handleCreateFile,
    handleCreateFolder,
    closeCreateDialog,
    addVirtualNode,
  };
};
