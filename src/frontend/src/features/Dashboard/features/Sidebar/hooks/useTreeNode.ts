import { useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { NodeType, ContainerNodeTree } from "@/types/project";
// import { useDeleteVirtualFolder } from "@/features/Dashboard/service/useProject";
// import { useQueryClient } from "@tanstack/react-query";
// import { toast } from "sonner";
// import { useThemeStore } from "@/features/Dashboard/store/useThemeStore";

export const useTreeNode = (node: ContainerNodeTree) => {
  const {
    selectedNode,
    setSelectedNode,
    activeNodeId,
    expandedNodeIds,
    toggleNodeExpansion,
    // addVirtualNode,
    // projectData,
  } = useProjectStore();

  // const { setTheme } = useThemeStore();

  // const queryClient = useQueryClient();
  // const deleteVirtualFolderMutation = useDeleteVirtualFolder(projectData?.id || "");

  const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setEditDialogOpen] = useState(false);
  const [isCreatePathDialogOpen, setCreatePathDialogOpen] = useState(false);
  const [nodeTypeToCreate, setNodeTypeToCreate] = useState<
    NodeType
  >("file");

  const isOpen = expandedNodeIds.includes(node._key);
  const isSelected = selectedNode?.id === node._key;
  const isActive = activeNodeId === node._key;
  const hasChildren = node.children && node.children.length > 0;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node._key);
  };

  const handleSelectNode = () => {
    if (selectedNode?.id === node._key) return;
    setSelectedNode({ id: node._key, type: node.node_type });
    // // Update global theme from the selected node if provided
    // setTheme(node.theme);
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
    // if (node.node_type !== "virtual_folder") return;
    // if (!projectData?.id) {
    //   toast.error("No project selected");
    //   return;
    // }
    // try {
    //   await deleteVirtualFolderMutation.mutateAsync(node.id);
    //   await Promise.all([
    //     // Avoid invalidating projectTree to preserve selection
    //     // queryClient.invalidateQueries({ queryKey: ["projectTree", projectData.id] }),
    //     queryClient.invalidateQueries({ queryKey: ["virtualFolders", projectData.id] }),
    //   ]);
    //   toast.success("Virtual folder removed");
    // } catch (error) {
    //   console.error("Failed to remove virtual folder:", error);
    //   toast.error("Failed to remove virtual folder");
    // }
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
    // addVirtualNode,
  };
};
