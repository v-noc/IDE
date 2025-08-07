import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";

interface NodeContextMenuProps {
  children: React.ReactNode;
  node: ProjectTreeResponse;
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
        {node.isVirtual && onEdit && (
          <ContextMenuItem onClick={onEdit}>Edit</ContextMenuItem>
        )}
        {(node.node_type == "function" || node.node_type == "class") && (
          <ContextMenuItem onClick={onCreatePath}>Create Path</ContextMenuItem>
        )}

        {node.node_type == "virtual_folder" && (
          <ContextMenuItem onClick={onRemove}>Remove</ContextMenuItem>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
};
