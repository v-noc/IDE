import { cn } from "@/lib/utils";

interface GeneratingShimmerProps {
  className?: string;
}

export function GeneratingShimmer({ className }: GeneratingShimmerProps) {
  return (
    <div className={cn("space-y-2", className)} aria-busy="true">
      <div className="h-3 w-full animate-pulse rounded bg-agent-bg-raised" />
      <div className="h-3 w-5/6 animate-pulse rounded bg-agent-bg-raised" />
      <div className="h-3 w-4/6 animate-pulse rounded bg-agent-bg-raised" />
      <p className="text-[11px] text-agent-text-muted">Generating…</p>
    </div>
  );
}
