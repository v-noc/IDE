import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { useTreeNode } from "./useTreeNode";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";
import CreateVirtualNodeDialog from "../VirtualFolders/CreateVirtualNodeDialog";
import EditVirtualFolderDialog from "../VirtualFolders/EditVirtualFolderDialog";
import CreatePathDialog from "../VirtualFolders/CreatePathDialog";

interface TreeNodeProps {
  node: ProjectTreeResponse;
  nestingLevel?: number;
}

export const TreeNode = ({ node, nestingLevel = 0 }: TreeNodeProps) => {
  const {
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
    handleCreatePath,
    closeCreateDialog,
    closeEditDialog,
    closeCreatePathDialog,
  } = useTreeNode(node);

  return (
    <>
      <NodeContextMenu
        node={node}
        onFocus={handleFocus}
        onExpand={handleExpand}
        onRemove={handleRemove}
        onEdit={node.isVirtual ? handleEdit : undefined}
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
          handleSelectNode={handleSelectNode}
        />
      </NodeContextMenu>
      <CreateVirtualNodeDialog
        isOpen={isCreateDialogOpen}
        onClose={closeCreateDialog}
        parentId={node.key}
        nodeType={nodeTypeToCreate}
      />
      <EditVirtualFolderDialog
        isOpen={isEditDialogOpen && !!node.isVirtual}
        onClose={closeEditDialog}
        node={node}
      />
      <CreatePathDialog
        isOpen={isCreatePathDialogOpen}
        onClose={closeCreatePathDialog}
        node={node}
      />
    </>
  );
};
