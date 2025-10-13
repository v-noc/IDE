import type { AnyNodeTree } from "@/types/project";
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
}

export const TreeNode = ({
  node,
  nestingLevel = 0,
  childFilter,
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
    closeCreatePathDialog,
  } = useTreeNode(node, childFilter);

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
          handleSelectNode={handleSelectNode}
          childFilter={childFilter}
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
        node={node}
      />
      {/* <CreatePathDialog
        isOpen={isCreatePathDialogOpen}
        onClose={closeCreatePathDialog}
        node={node}
      /> */}
    </>
  );
};
