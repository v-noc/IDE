import { useMemo, useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { NodeType, AnyNodeTree, ContainerNodeTree } from "@/types/project";
import { useAddCall, useRemoveCall } from "@/features/Dashboard/service/useCall";
// import { useDeleteVirtualFolder } from "@/features/Dashboard/service/useProject";
// import { useQueryClient } from "@tanstack/react-query";
// import { toast } from "sonner";
// import { useThemeStore } from "@/features/Dashboard/store/useThemeStore";

export const useTreeNode = (
  node: ContainerNodeTree,
  childFilter: (node: ContainerNodeTree) => boolean = () => true,
) => {
  const {
    selectedNode,
    secondarySelectedNode,
    setSelectedNode,
    setSecondarySelectedNode,
    pushFocus,
    activeNodeId,
    expandedNodeIds,
    toggleNodeExpansion,
    projectData,
    focusStack
    // addVirtualNode,
    // projectData,
  } = useProjectStore();
  const addCallMutation = useAddCall(node._key, projectData?._key || "");
  const removeCallMutation = useRemoveCall(node._key, projectData?._key || "");

  // const queryClient = useQueryClient();
  // const deleteVirtualFolderMutation = useDeleteVirtualFolder(projectData?.id || "");

  const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setEditDialogOpen] = useState(false);
  const [isCreatePathDialogOpen, setCreatePathDialogOpen] = useState(false);
  const [nodeTypeToCreate, setNodeTypeToCreate] = useState<
    NodeType
  >("file");


  const isOpen = expandedNodeIds.includes(node._key);
  const isSelected =
    selectedNode?._key === node._key || secondarySelectedNode?._key === node._key;
  const isActive = activeNodeId === node._key;
  const hasChildren = useMemo(() => {
    const children = node.children ?? [];
    return children.some(childFilter);
  }, [node, childFilter]);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node._key);
  };

  const handleSelectNode = () => {

    if (selectedNode?._key === node._key) return;
    setSelectedNode(node);
    // Clear any secondary selection when a primary selection is made
    if (secondarySelectedNode)
      setSecondarySelectedNode(null);
    // // Update global theme from the selected node if provided
    // setTheme(node.theme);
  };

  const handleFocus = () => {
    if (focusStack.length > 0) {
      if (focusStack[focusStack.length - 1]._key === node._key) {
        return;
      }
    }
    pushFocus(node);
  };

  const handleExpand = () => {
    toggleNodeExpansion(node._key);

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

  const handleAddCall = (node: AnyNodeTree) => {
    console.log("handleAddCall");
    addCallMutation.mutate({
      callee_target_id: node._key,
      name: node.name,
      description: node.description,
    });
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

  const handleRemoveCall = (node: AnyNodeTree) => {
    removeCallMutation.mutate(node._key);
  };

  const closeEditDialog = () => {
    setEditDialogOpen(false);
  };

  return {
    isOpen,
    projectData,
    isSelected,
    isActive,
    hasChildren,
    isCreateDialogOpen,
    isEditDialogOpen,
    isCreatePathDialogOpen,
    nodeTypeToCreate,
    handleEdit,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
    handleAddCall,
    handleCreateFile,
    handleCreateFolder,
    handleCreatePath,
    closeCreateDialog,
    closeEditDialog,
    closeCreatePathDialog,
    handleRemoveCall
    // addVirtualNode,
  };
};
