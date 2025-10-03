import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import type { ContainerNodeTree } from "@/types/project";

interface NodeContextMenuProps {
  children: React.ReactNode;
  node: ContainerNodeTree;
  onFocus: () => void;
  onExpand: () => void;
  onRemove: () => void;

  onCreatePath: () => void;
  onEdit?: () => void;
}

export const NodeContextMenu = ({
  children,
  node,
  onFocus,
  onExpand,
  onRemove,
  onCreatePath,
  onEdit,
}: NodeContextMenuProps) => {
  return (
    <ContextMenu>
      <ContextMenuTrigger>{children}</ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem onClick={onFocus}>Focus</ContextMenuItem>
        <ContextMenuItem onClick={onExpand}>Expand</ContextMenuItem>
        {onEdit && <ContextMenuItem onClick={onEdit}>Edit</ContextMenuItem>}
        {(node.node_type == "function" ||
          node.node_type == "class" ||
          node.node_type == "file" ||
          node.node_type == "folder") && (
          <ContextMenuItem onClick={onCreatePath}>Create Path</ContextMenuItem>
        )}

        {node.node_type == "folder" && (
          <ContextMenuItem onClick={onRemove}>Remove</ContextMenuItem>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
};
