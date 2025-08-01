import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { useTreeNode } from "./useTreeNode";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";
import CreateVirtualNodeDialog from "../CustomFolders/CreateVirtualNodeDialog";

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
    nodeTypeToCreate,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
    handleCreateFile,
    handleCreateFolder,
    closeCreateDialog,
  } = useTreeNode(node);

  return (
    <>
      <NodeContextMenu
        node={node}
        onFocus={handleFocus}
        onExpand={handleExpand}
        onRemove={handleRemove}
        onCreateFile={handleCreateFile}
        onCreateFolder={handleCreateFolder}
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
    </>
  );
};
