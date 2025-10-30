import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Separator } from "@/components/ui/separator";
import type { AnyNodeTree } from "@/types/project";
import { Crosshair, Expand, Link, Trash } from "lucide-react";

interface NodeContextMenuProps {
  children: React.ReactNode;
  node: AnyNodeTree;
  onFocus: () => void;
  onExpand: () => void;
  onRemove: () => void;
  onRemoveCall: () => void;
  onAddCall: () => void;
  onEdit?: () => void;
}

export const NodeContextMenu = ({
  children,
  node,
  onFocus,
  onExpand,
  onAddCall,
  onRemoveCall,
}: NodeContextMenuProps) => {
  return (
    <ContextMenu>
      <ContextMenuTrigger>
        <div>{children}</div>
      </ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem onClick={onFocus}>
          <Crosshair />
          Focus
        </ContextMenuItem>
        <ContextMenuItem onClick={onExpand}>
          <Expand />
          Expand
        </ContextMenuItem>
        <Separator />
        {(node.node_type == "function" ||
          node.node_type == "class" ||
          node.node_type == "call" ||
          node.node_type == "file") && (
          <ContextMenuItem onClick={onAddCall}>
            <Link />
            Add Call
          </ContextMenuItem>
        )}
        {node.node_type === "call" && node?.manually_created && (
          <ContextMenuItem onClick={() => onRemoveCall()}>
            <Trash />
            Remove Call
          </ContextMenuItem>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
};
