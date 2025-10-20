import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import type React from "react";
import { useTreeNode } from "../../hooks/useTreeNode";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";
import CreateVirtualNodeDialog from "../VirtualFolders/CreateVirtualNodeDialog";
import EditVirtualFolderDialog from "../VirtualFolders/EditVirtualFolderDialog";
// import CreatePathDialog from "../VirtualFolders/CreatePathDialog";

interface TreeNodeProps {
  node: AnyNodeTree;
  nestingLevel?: number;
  childFilter?: (node: AnyNodeTree) => boolean;
  onSelect?: (node: AnyNodeTree) => void;
  rightAdornment?: React.ReactNode | ((node: AnyNodeTree) => React.ReactNode);
}

export const TreeNode = ({
  node,
  nestingLevel = 0,
  childFilter,
  onSelect,
  rightAdornment,
}: TreeNodeProps) => {
  const {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
    isCreateDialogOpen,
    isEditDialogOpen,
    // isCreatePathDialogOpen,
    nodeTypeToCreate,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
    // handleEdit,
    handleCreatePath,
    closeCreateDialog,
    closeEditDialog,
    // closeCreatePathDialog,
  } = useTreeNode(node, childFilter);

  const handleSelectOverride = onSelect
    ? () => onSelect(node)
    : handleSelectNode;

  return (
    <>
      <NodeContextMenu
        node={node}
        onFocus={handleFocus}
        onExpand={handleExpand}
        onRemove={handleRemove}
        onEdit={undefined}
        onCreatePath={handleCreatePath}
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
          rightAdornment={rightAdornment}
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
      {/* <CreatePathDialog
        isOpen={isCreatePathDialogOpen}
        onClose={closeCreatePathDialog}
        node={node}
      /> */}
    </>
  );
};
