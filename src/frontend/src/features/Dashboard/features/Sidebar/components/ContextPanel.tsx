import { memo } from "react";
import { cn } from "@/lib/utils";
import { FolderTree, X, Box } from "lucide-react";
import ProjectTree from "./ProjectTree";
import type { TabData } from "@/types/tabs";

import type { AnyNodeTree } from "@/types/project";

interface ContextPanelProps {
  tab: TabData;
  projectTree: AnyNodeTree;
  isActive: boolean;
  onActivate: () => void;
  onClose?: () => void;
}

export const ContextPanel = memo(function ContextPanel({
  tab,
  projectTree,
  isActive,
  onActivate,
  onClose,
}: ContextPanelProps) {
  if (!projectTree) return null;

  const isRoot = tab.id === "root";
  const Icon = isRoot ? FolderTree : Box;

  return (
    <div
      className={cn(
        "flex flex-col border-b last:border-b-0 h-full w-full",
        isActive ? "bg-background" : "bg-muted/10 opacity-70"
      )}
      onClick={onActivate}
    >
      {/* Header */}
      <div
        className={cn(
          "flex items-center px-3 py-2 border-b select-none cursor-pointer transition-colors",
          isActive ? "bg-primary/5 border-primary/20" : "hover:bg-accent/50"
        )}
      >
        <Icon
          className={cn(
            "size-3.5 mr-2",
            isActive ? "text-primary" : "text-muted-foreground"
          )}
        />
        <span
          className={cn(
            "text-[11px] font-semibold uppercase tracking-wider truncate flex-1",
            isActive ? "text-foreground" : "text-muted-foreground"
          )}
        >
          {tab.title}
        </span>

        {onClose && !isRoot && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="p-1 rounded-sm hover:bg-destructive/10 hover:text-destructive text-muted-foreground transition-colors"
          >
            <X className="size-3" />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-2">
        <ProjectTree projectTree={projectTree} tabId={tab.id} />
      </div>
    </div>
  );
});
