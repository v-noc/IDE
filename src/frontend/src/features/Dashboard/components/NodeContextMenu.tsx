import { useRef } from "react";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Separator } from "@/components/ui/separator";
import { Crosshair, Expand, Group, Link, Link2, Trash, FileCode, ListTodo } from "lucide-react";

interface NodeContextMenuProps {
  children: React.ReactNode;
  nodeId: string;
  nodeType: string;
  manuallyCreated?: boolean;
  onAction: (action: string) => void;
}

// Radix flips the menu above the cursor when there's no room below (e.g. near the
// bottom of the screen). The flip can land a menu item right under the cursor at the
// moment it opens, so the pointerup that ends the right-click immediately "selects"
// it. Ignore selections for a brief window after open to avoid that phantom click.
const OPEN_GUARD_MS = 200;

export const NodeContextMenu = ({
  children,
  nodeId,
  nodeType,
  manuallyCreated,
  onAction,
}: NodeContextMenuProps) => {
  const openedAtRef = useRef(0);

  const guardedAction = (action: string) => (event: Event) => {
    if (Date.now() - openedAtRef.current < OPEN_GUARD_MS) {
      event.preventDefault();
      return;
    }
    onAction(action);
  };

  return (
    <ContextMenu
      onOpenChange={(open) => {
        if (open) openedAtRef.current = Date.now();
      }}
    >
      <ContextMenuTrigger asChild>
        <div>{children}</div>
      </ContextMenuTrigger>
      <ContextMenuContent data-node-id={nodeId}>
        <ContextMenuItem onSelect={guardedAction("focus")}>
          <Crosshair className="mr-2 h-4 w-4" />
          Focus
        </ContextMenuItem>
        <ContextMenuItem onSelect={guardedAction("expand")}>
          <Expand className="mr-2 h-4 w-4" />
          Expand
        </ContextMenuItem>
        <ContextMenuItem onSelect={guardedAction("copy-link")}>
          <Link2 className="mr-2 h-4 w-4" />
          Copy link
        </ContextMenuItem>
        <ContextMenuItem onSelect={guardedAction("prompt-builder")}>
          <FileCode className="mr-2 h-4 w-4" />
          Build Prompt
        </ContextMenuItem>
        <ContextMenuItem onSelect={guardedAction("new-task")}>
          <ListTodo className="mr-2 h-4 w-4" />
          New task here
        </ContextMenuItem>
        <Separator />
        {["function", "class", "call", "file"].includes(nodeType) && (
          <ContextMenuItem onSelect={guardedAction("add-call")}>
            <Link className="mr-2 h-4 w-4" />
            Add Call
          </ContextMenuItem>
        )}
        {nodeType === "call" && manuallyCreated && (
          <ContextMenuItem onSelect={guardedAction("remove-call")}>
            <Trash className="mr-2 h-4 w-4" />
            Remove Call
          </ContextMenuItem>
        )}
        {nodeType === "group" && (
          <>
            <ContextMenuItem onSelect={guardedAction("manage-group")}>
              <Group className="mr-2 h-4 w-4" />
              Edit Group
            </ContextMenuItem>
            <ContextMenuItem onSelect={guardedAction("delete-group")}>
              <Trash className="mr-2 h-4 w-4" />
              Delete Group
            </ContextMenuItem>
          </>
        )}
        {nodeType !== "project" && (
          <ContextMenuItem onSelect={guardedAction("create-group")}>
            <Group className="mr-2 h-4 w-4" />
            Create Group
          </ContextMenuItem>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
};

