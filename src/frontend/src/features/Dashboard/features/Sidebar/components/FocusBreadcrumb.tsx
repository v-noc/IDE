import { memo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useShallow } from "zustand/react/shallow";

interface FocusBreadcrumbProps {
  tabId: string;
}

export const FocusBreadcrumb = memo(function FocusBreadcrumb({
  tabId,
}: FocusBreadcrumbProps) {
  // Selectors - only subscribe to what's needed
  const focusedNode = useProjectStore((s) => s.focusedNode[tabId]);
  const focusStack = useProjectStore(
    useShallow((s) => s.focusStack[tabId] ?? [])
  );
  const popFocus = useProjectStore((s) => s.popFocus);
  const clearFocus = useProjectStore((s) => s.clearFocus);

  if (!focusedNode) return null;

  return (
    <div className="flex items-center justify-between px-2 py-1 bg-muted/40 border rounded">
      <div className="text-xs text-muted-foreground truncate">
        Focus: {focusStack.map((n) => n.name).join(" / ")}
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="text-xs px-2 py-0.5 rounded border hover:bg-accent"
          onClick={() => popFocus(tabId)}
        >
          Back
        </button>
        <button
          type="button"
          className="text-xs px-2 py-0.5 rounded border hover:bg-accent"
          onClick={() => clearFocus(tabId)}
        >
          Clear
        </button>
      </div>
    </div>
  );
});
