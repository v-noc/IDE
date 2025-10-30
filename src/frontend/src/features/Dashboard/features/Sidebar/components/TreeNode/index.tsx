import { type NodeType, type ContainerNodeTree } from "@/types/project";
import { useTreeNode } from "../../hooks/useTreeNode";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";
import CreateVirtualNodeDialog from "../VirtualFolders/CreateVirtualNodeDialog";
import EditVirtualFolderDialog from "../VirtualFolders/EditVirtualFolderDialog";
import { useState } from "react";
import SelectNodeDialog from "../SelectNodeDialog";
// import CreatePathDialog from "../VirtualFolders/CreatePathDialog";

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
    handleRemove,
    // handleEdit,
    handleAddCall,
    closeCreateDialog,
    handleRemoveCall,
    closeEditDialog,
    // closeCreatePathDialog,
  } = useTreeNode(node, childFilter);

  const [isAddCallDialogOpen, setIsAddCallDialogOpen] = useState<{
    node_id: string;
    node_type: NodeType;
  } | null>(null);

  const closeAddCallDialog = () => {
    setIsAddCallDialogOpen(null);
  };

  const handleSelectOverride = onSelect
    ? () => onSelect(node)
    : handleSelectNode;

  return (
    <>
      <NodeContextMenu
        node={node}
        onFocus={handleFocus}
        onExpand={handleExpand}
        onRemoveCall={() => {
          handleRemoveCall(node);
        }}
        onRemove={handleRemove}
        onEdit={undefined}
        onAddCall={() =>
          setIsAddCallDialogOpen({
            node_id: node._key,
            node_type: node.node_type,
          })
        }
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
        list={projectData?.children ?? []}
        selectNodeType={["function"]}
        onSelect={(node) => handleAddCall(node)}
      />
    </>
  );
};
