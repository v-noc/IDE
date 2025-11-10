import { type NodeType, type ContainerNodeTree } from "@/types/project";
import { useTreeNode } from "../../hooks/useTreeNode";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";
import CreateVirtualNodeDialog from "../VirtualFolders/CreateVirtualNodeDialog";
import EditVirtualFolderDialog from "../VirtualFolders/EditVirtualFolderDialog";
import { useState } from "react";
import SelectNodeDialog from "../SelectNodeDialog";
import CreateGroupsDialog from "@/features/Dashboard/components/CreateGroupsDialog";
import type { AnyNodeTree, CallNodeTree, GroupNodeTree } from "@/types/project";
import ManageGroupsDialog from "@/features/Dashboard/components/ManageGroupsDialog";
// import CreatePathDialog from "../VirtualFolders/CreatePathDialog";
import PromptBuilder from "@/components/PromptBuilder/PromptBuilder";

interface TreeNodeProps {
  node: ContainerNodeTree;
  nestingLevel?: number;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const TreeNode = ({
  node,
  nestingLevel = 0,
  childFilter,
  onSelect,
}: TreeNodeProps) => {
  const {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
    projectData,
    isCreateDialogOpen,
    isEditDialogOpen,
    // isCreatePathDialogOpen,
    nodeTypeToCreate,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,

    // handleEdit,
    handleAddCall,
    closeCreateDialog,
    handleRemoveCall,
    closeEditDialog,
    handleDeleteGroup,
    // closeCreatePathDialog,
  } = useTreeNode(node, childFilter);

  const [isAddCallDialogOpen, setIsAddCallDialogOpen] = useState<{
    node_id: string;
    node_type: NodeType;
  } | null>(null);

  const [isCreateGroupsDialogOpen, setIsCreateGroupsDialogOpen] =
    useState(false);
  const [isManageGroupsDialogOpen, setIsManageGroupsDialogOpen] =
    useState(false);

  const [isPromptBuilderOpen, setIsPromptBuilderOpen] = useState(false);

  const closeAddCallDialog = () => {
    setIsAddCallDialogOpen(null);
  };

  const getParentNode = (
    node: ContainerNodeTree,
    currentNode: ContainerNodeTree
  ): ContainerNodeTree | null => {
    if (currentNode.children?.some((child) => child._key === node._key)) {
      return currentNode;
    }
    for (const child of currentNode.children ?? []) {
      const parent = getParentNode(node, child as ContainerNodeTree);
      if (parent) {
        return parent;
      }
    }

    return null;
  };

  const getSiblings = (node: ContainerNodeTree): ContainerNodeTree[] => {
    const parentNode = getParentNode(node, projectData as ContainerNodeTree);
    if (!parentNode) return [];
    const children = parentNode.children ?? [];
    return children.filter(
      (child) => child._key !== node._key
    ) as ContainerNodeTree[];
  };

  const handleSelectOverride = onSelect
    ? () => onSelect(node)
    : handleSelectNode;

  return (
    <>
      <NodeContextMenu
        node={node as AnyNodeTree}
        onFocus={handleFocus}
        onExpand={handleExpand}
        onCreateGroup={() => {}}
        onDeleteGroup={() => {}}
        onRemoveCall={() => {}}
        onManageGroup={() => setIsManageGroupsDialogOpen(true)}
        onEdit={undefined}
        onBuildPrompt={() => setIsPromptBuilderOpen(true)}
        onAddCall={() => {}}
      >
        <NodeContent
          node={node}
          isOpen={isOpen}
          isSelected={isSelected}
          isActive={isActive}
          hasChildren={hasChildren}
          nestingLevel={nestingLevel}
          handleToggle={handleToggle}
          handleSelectNode={handleSelectOverride}
          childFilter={childFilter}
          onSelect={onSelect}
        />
      </NodeContextMenu>
      <CreateVirtualNodeDialog
        isOpen={isCreateDialogOpen}
        onClose={closeCreateDialog}
        parentId={node._key}
        nodeType={nodeTypeToCreate}
      />
      <EditVirtualFolderDialog
        isOpen={isEditDialogOpen}
        onClose={closeEditDialog}
        node={node as unknown as ContainerNodeTree}
      />

      <SelectNodeDialog
        isOpen={isAddCallDialogOpen !== null}
        onClose={closeAddCallDialog}
        list={(projectData?.children as AnyNodeTree[]) ?? []}
        selectNodeType={["function"]}
        onSelect={(node) => handleAddCall(node)}
      />

      <CreateGroupsDialog
        isOpen={isCreateGroupsDialogOpen}
        onClose={() => setIsCreateGroupsDialogOpen(false)}
        initialChildren={node ? [node as AnyNodeTree] : []}
        project_key={projectData?._key ?? ""}
        parent_node_id={
          getParentNode(node, projectData as ContainerNodeTree)?._key ?? ""
        }
      />

      <ManageGroupsDialog
        isOpen={isManageGroupsDialogOpen}
        onClose={() => setIsManageGroupsDialogOpen(false)}
        group={node as unknown as GroupNodeTree}
        siblings={getSiblings(node as ContainerNodeTree) as AnyNodeTree[]}
        project_key={projectData?._key ?? ""}
      />

      <PromptBuilder
        open={isPromptBuilderOpen}
        onOpenChange={setIsPromptBuilderOpen}
        rootNode={node as ContainerNodeTree}
      />
    </>
  );
};
