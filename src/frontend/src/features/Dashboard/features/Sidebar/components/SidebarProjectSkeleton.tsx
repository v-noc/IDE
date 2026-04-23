import { memo } from "react";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Placeholder while project structure is loading or store has not caught up with the route.
 */
export const SidebarProjectSkeleton = memo(function SidebarProjectSkeleton() {
  return (
    <div className="flex flex-col h-full min-h-0 border-b border-border overflow-hidden">
      <div className="flex items-center px-3 py-2 border-b border-border gap-2 shrink-0">
        <Skeleton className="size-3.5 shrink-0 rounded" />
        <Skeleton className="h-3 w-24 rounded" />
      </div>
      <div className="flex-1 overflow-auto p-2 space-y-2 min-h-0">
        {Array.from({ length: 9 }, (_, i) => (
          <div
            key={i}
            className="flex items-center gap-2"
            style={{ paddingLeft: `${Math.min(i, 4) * 10}px` }}
          >
            <Skeleton className="size-4 shrink-0 rounded" />
            <Skeleton
              className="h-3.5 rounded-md flex-1"
              style={{ maxWidth: `${52 + ((i * 7) % 35)}%` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
});
