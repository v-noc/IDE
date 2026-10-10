import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface CoverageSummaryProps {
  total: number;
  coveredCount: number;
  /** Hide the progress bar and line count for tight spaces (e.g. a toolbar). */
  compact?: boolean;
  className?: string;
}

function coverageTone(percent: number) {
  if (percent >= 80) {
    return "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30";
  }
  if (percent >= 50) {
    return "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30";
  }
  return "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30";
}

export default function CoverageSummary({
  total,
  coveredCount,
  compact = false,
  className,
}: CoverageSummaryProps) {
  const percent = total > 0 ? Math.round((coveredCount / total) * 100) : 0;

  const badge = (
    <span
      className={cn(
        "text-xs font-semibold rounded-full border px-2 py-0.5 shrink-0 whitespace-nowrap",
        coverageTone(percent),
      )}
    >
      {percent}% covered
    </span>
  );

  if (compact) {
    return <div className={className}>{badge}</div>;
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {badge}
      <Progress value={percent} className="h-1.5 flex-1" />
      <span className="text-[11px] text-muted-foreground whitespace-nowrap">
        {coveredCount}/{total} lines
      </span>
    </div>
  );
}
