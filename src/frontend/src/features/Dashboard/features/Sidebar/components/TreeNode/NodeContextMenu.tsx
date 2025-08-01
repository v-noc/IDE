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
  onCreateFile: () => void;
  onCreateFolder: () => void;
}

export const NodeContextMenu = ({
  children,
  node,
  onFocus,
  onExpand,
  onRemove,
  onCreateFile,
  onCreateFolder,
}: NodeContextMenuProps) => {
  return (
    <ContextMenu>
      <ContextMenuTrigger>{children}</ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem onClick={onFocus}>Focus</ContextMenuItem>
        <ContextMenuItem onClick={onExpand}>Expand</ContextMenuItem>
        <ContextMenuItem onClick={onRemove}>Remove</ContextMenuItem>
        {node.isVirtual && node.node_type === "folder" && (
          <>
            <ContextMenuItem onClick={onCreateFile}>
              Create File
            </ContextMenuItem>
            <ContextMenuItem onClick={onCreateFolder}>
              Create Folder
            </ContextMenuItem>
          </>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
};
