import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Separator } from "@/components/ui/separator";
import type { AnyNodeTree } from "@/types/project";
import { Crosshair, Expand, Group, Link, Trash, FileCode } from "lucide-react";
import { useState } from "react";
import { ConfirmDialog } from "@/components/ConfirmDialog";

interface NodeContextMenuProps {
  children: React.ReactNode;
  node: AnyNodeTree;
  onFocus: () => void;
  onExpand: () => void;
  onRemove: () => void;
  onRemoveCall: () => void;
  onAddCall: () => void;
  onEdit?: () => void;
  onCreateGroup: () => void;
  onDeleteGroup: () => void;
  onManageGroup?: () => void;
  onBuildPrompt?: () => void;
}

export const NodeContextMenu = ({
  children,
  node,
  onFocus,
  onExpand,
  onAddCall,
  onRemoveCall,
  onCreateGroup,
  onManageGroup,
  onDeleteGroup,
  onBuildPrompt,
}: NodeContextMenuProps) => {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  return (
    <>
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
          {onBuildPrompt && (
            <ContextMenuItem onClick={onBuildPrompt}>
              <FileCode />
              Build Prompt
            </ContextMenuItem>
          )}
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
          {node.node_type === "group" && onManageGroup && (
            <>
              <ContextMenuItem onClick={onManageGroup}>
                <Group />
                Edit Group
              </ContextMenuItem>
              <ContextMenuItem onClick={() => setIsDeleteDialogOpen(true)}>
                <Trash />
                Delete Group
              </ContextMenuItem>
            </>
          )}
          {node.node_type !== "project" && (
            <ContextMenuItem onClick={onCreateGroup}>
              <Group />
              Create Group
            </ContextMenuItem>
          )}
        </ContextMenuContent>
      </ContextMenu>
      <ConfirmDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
        title="Delete this group?"
        description="This action cannot be undone. This will permanently remove the group and its associations."
        confirmLabel="Delete"
        actionClassName="bg-destructive text-destructive-foreground hover:bg-destructive/90"
        onConfirm={onDeleteGroup}
      />
    </>
  );
};
