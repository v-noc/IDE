import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";

interface NodeContextMenuProps {
  children: React.ReactNode;
  onFocus: () => void;
  onExpand: () => void;
  onRemove: () => void;
}

export const NodeContextMenu = ({
  children,
  onFocus,
  onExpand,
  onRemove,
}: NodeContextMenuProps) => {
  return (
    <ContextMenu>
      <ContextMenuTrigger>{children}</ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem onClick={onFocus}>Focus</ContextMenuItem>
        <ContextMenuItem onClick={onExpand}>Expand</ContextMenuItem>
        <ContextMenuItem onClick={onRemove}>Remove</ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
};
