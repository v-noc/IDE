import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Separator } from "@/components/ui/separator";
import { Crosshair, Expand, Group, Link, Trash, FileCode } from "lucide-react";

interface NodeContextMenuProps {
  children: React.ReactNode;
  nodeId: string;
  nodeType: string;
  manuallyCreated?: boolean;
  onAction: (action: string) => void;
}

export const NodeContextMenu = ({
  children,
  nodeId,
  nodeType,
  manuallyCreated,
  onAction,
}: NodeContextMenuProps) => {

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <div>{children}</div>
      </ContextMenuTrigger>
      <ContextMenuContent data-node-id={nodeId}>
        <ContextMenuItem onClick={() => onAction("focus")}>
          <Crosshair className="mr-2 h-4 w-4" />
          Focus
        </ContextMenuItem>
        <ContextMenuItem onClick={() => onAction("expand")}>
          <Expand className="mr-2 h-4 w-4" />
          Expand
        </ContextMenuItem>
        <ContextMenuItem onClick={() => onAction("prompt-builder")}>
          <FileCode className="mr-2 h-4 w-4" />
          Build Prompt
        </ContextMenuItem>
        <Separator />
        {["function", "class", "call", "file"].includes(nodeType) && (
          <ContextMenuItem onClick={() => onAction("add-call")}>
            <Link className="mr-2 h-4 w-4" />
            Add Call
          </ContextMenuItem>
        )}
        {nodeType === "call" && manuallyCreated && (
          <ContextMenuItem onClick={() => onAction("remove-call")}>
            <Trash className="mr-2 h-4 w-4" />
            Remove Call
          </ContextMenuItem>
        )}
        {nodeType === "group" && (
          <>
            <ContextMenuItem onClick={() => onAction("manage-group")}>
              <Group className="mr-2 h-4 w-4" />
              Edit Group
            </ContextMenuItem>
            <ContextMenuItem onClick={() => onAction("delete-group")}>
              <Trash className="mr-2 h-4 w-4" />
              Delete Group
            </ContextMenuItem>
          </>
        )}
        {nodeType !== "project" && (
          <ContextMenuItem onClick={() => onAction("create-group")}>
            <Group className="mr-2 h-4 w-4" />
            Create Group
          </ContextMenuItem>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
};

