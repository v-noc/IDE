import { useMemo } from "react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface CoverageViewProps {
  source: string;
  /** Absolute 1-based line number the source snippet starts at. */
  startLine: number;
  /** Absolute line numbers (1-based, file-relative) that tests executed. */
  coveredLines: number[];
  targetFunctionName?: string;
  isLoading?: boolean;
  isError?: boolean;
}

function coverageTone(percent: number) {
  if (percent >= 80) {
    return {
      text: "text-emerald-600 dark:text-emerald-400",
      badge:
        "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    };
  }
  if (percent >= 50) {
    return {
      text: "text-amber-600 dark:text-amber-400",
      badge:
        "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
    };
  }
  return {
    text: "text-red-600 dark:text-red-400",
    badge: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30",
  };
}

export default function CoverageView({
  source,
  startLine,
  coveredLines,
  targetFunctionName,
  isLoading = false,
  isError = false,
}: CoverageViewProps) {
  const lines = useMemo(() => source.split("\n"), [source]);
  const coveredSet = useMemo(() => new Set(coveredLines), [coveredLines]);

  const total = lines.length;
  const coveredCount = useMemo(() => {
    let count = 0;
    for (let i = 0; i < total; i++) {
      if (coveredSet.has(startLine + i)) count++;
    }
    return count;
  }, [coveredSet, startLine, total]);

  const percent = total > 0 ? Math.round((coveredCount / total) * 100) : 0;
  const hasData = total > 0 && !isLoading && !isError;
  const tone = coverageTone(percent);

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
        Loading coverage...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
        Failed to load coverage for this function.
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
        No coverage data yet. Run tests to see line coverage.
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col gap-2">
      <div className="px-1 shrink-0 space-y-1.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground truncate">
            {targetFunctionName
              ? `Lines executed in ${targetFunctionName}`
              : "Lines executed by tests"}
          </span>
          <span
            className={cn(
              "text-xs font-semibold rounded-full border px-2 py-0.5 shrink-0",
              tone.badge
            )}
          >
            {percent}% covered
          </span>
        </div>
        <Progress value={percent} className="h-1.5" />
        <div className="text-[11px] text-muted-foreground">
          {coveredCount} of {total} lines covered
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-auto rounded-md border border-border bg-muted/20">
        <table className="w-full border-collapse font-mono text-xs">
          <tbody>
            {lines.map((line, i) => {
              const lineNo = startLine + i;
              const isCovered = coveredSet.has(lineNo);
              return (
                <tr key={lineNo} className={isCovered ? "bg-emerald-500/10" : undefined}>
                  <td
                    className={cn(
                      "select-none text-right pr-2 pl-2 align-top text-muted-foreground/70 border-r",
                      isCovered
                        ? "border-emerald-500/40"
                        : "border-transparent"
                    )}
                    style={{ width: 44 }}
                  >
                    {lineNo}
                  </td>
                  <td className="pl-2 pr-3 align-top whitespace-pre text-foreground/90">
                    {line.length > 0 ? line : " "}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
