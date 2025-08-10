import { useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { NodeType, ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { useDeleteVirtualFolder } from "@/features/Dashboard/service/useProject";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useThemeStore } from "@/features/Dashboard/store/useThemeStore";

export const useTreeNode = (node: ProjectTreeResponse) => {
  const {
    selectedNode,
    setSelectedNode,
    activeNodeId,
    expandedNodeIds,
    toggleNodeExpansion,
    addVirtualNode,
    projectData,
  } = useProjectStore();

  const { setTheme } = useThemeStore();

  const queryClient = useQueryClient();
  const deleteVirtualFolderMutation = useDeleteVirtualFolder(projectData?.key || "");

  const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setEditDialogOpen] = useState(false);
  const [isCreatePathDialogOpen, setCreatePathDialogOpen] = useState(false);
  const [nodeTypeToCreate, setNodeTypeToCreate] = useState<
    NodeType
  >("file");

  const isOpen = expandedNodeIds.includes(node.key);
  const isSelected = selectedNode?.id === node.key;
  const isActive = activeNodeId === node.key;
  const hasChildren = node.children && node.children.length > 0;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node.key);
  };

  const handleSelectNode = () => {
    if (selectedNode?.id === node.key) return;
    setSelectedNode({ id: node.key, type: node.node_type });
    // Update global theme from the selected node if provided
    setTheme(node.theme);
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

  const handleRemove = async () => {
    if (node.node_type !== "virtual_folder") return;
    if (!projectData?.key) {
      toast.error("No project selected");
      return;
    }
    try {
      await deleteVirtualFolderMutation.mutateAsync(node.key);
      await Promise.all([
        // Avoid invalidating projectTree to preserve selection
        // queryClient.invalidateQueries({ queryKey: ["projectTree", projectData.key] }),
        queryClient.invalidateQueries({ queryKey: ["virtualFolders", projectData.key] }),
      ]);
      toast.success("Virtual folder removed");
    } catch (error) {
      console.error("Failed to remove virtual folder:", error);
      toast.error("Failed to remove virtual folder");
    }
  };

  const handleEdit = () => {
    setEditDialogOpen(true);
  };

  const handleCreateFile = () => {
    setNodeTypeToCreate("file");
    setCreateDialogOpen(true);
  };

  const handleCreateFolder = () => {
    setNodeTypeToCreate("folder");
    setCreateDialogOpen(true);
  };

  const handleCreatePath = () => {
    setCreatePathDialogOpen(true);
  };

  const closeCreateDialog = () => {
    setCreateDialogOpen(false);
  };

  const closeCreatePathDialog = () => {
    setCreatePathDialogOpen(false);
  };

  const closeEditDialog = () => {
    setEditDialogOpen(false);
  };

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
    isCreateDialogOpen,
    isEditDialogOpen,
    isCreatePathDialogOpen,
    nodeTypeToCreate,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
    handleEdit,
    handleCreateFile,
    handleCreateFolder,
    handleCreatePath,
    closeCreateDialog,
    closeEditDialog,
    closeCreatePathDialog,
    addVirtualNode,
  };
};
