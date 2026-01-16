import React, { useState } from "react";
import { LogRow } from "./components/LogRow";
import { useLogsState } from "./hooks/useLogsState";
import { FlameGraph } from "@/components/FlameGraph";
import { mapLogToFlameNode } from "./utils/mapping";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { type LogTreeNode } from "@/services/logs";
import { useResizeObserver } from "@/hooks/useResizeObserver";
import { useNodeRevealer } from "./hooks/useNodeRevealer";
import type { LogNode } from "@/services/logs/api";

/**
 * Logs Feature.
 * Selection-based log viewer for execution traces.
 */
export const LogsContainer: React.FC<{ tabId: string }> = ({ tabId }) => {
  const { logs, isLoading, hasSelection } = useLogsState(tabId);
  const [viewMode, setViewMode] = useState<"list" | "chart">("list");
  const [selectedLogForChart, setSelectedLogForChart] =
    useState<LogTreeNode | null>(null);
  const { ref, width } = useResizeObserver();
  const { revealNode } = useNodeRevealer(tabId);

  const handleViewFlameChart = (node: LogTreeNode) => {
    setSelectedLogForChart(node);
    setViewMode("chart");
  };

  const handleBackToList = () => {
    setViewMode("list");
    setSelectedLogForChart(null);
  };

  if (!hasSelection) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8 text-center text-sm text-muted-foreground bg-white/50 rounded-md border border-dashed">
        Select a function or call in the workspace to view execution logs.
      </div>
    );
  }

  if (viewMode === "chart" && selectedLogForChart) {
    return (
      <div
        className="w-full h-full flex flex-col bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm"
        ref={ref}
      >
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 p-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackToList}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900"
          >
            <ArrowLeft className="size-4" />
            Back to List
          </Button>
          <span className="text-xs font-medium text-slate-500">
            Trace: {selectedLogForChart.message || selectedLogForChart._id}
          </span>
          <div className="w-20" /> {/* Spacer for balance */}
        </div>
        <div className="flex-1 overflow-auto p-4">
          <FlameGraph
            data={[mapLogToFlameNode(selectedLogForChart)]}
            width={width - 32} // Padding adjustment
            rowHeight={20}
            onSelect={(n) => {
              if (n.functionId && selectedLogForChart) {
                // Map FlameGraphNode back to a partial LogNode for revealNode

                revealNode(
                  { function_id: n.functionId } as LogNode,
                  selectedLogForChart
                );
              }
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-slate-50 border border-slate-200 rounded-lg overflow-hidden shadow-sm">
      {/* Header - Fixed */}
      <div className="flex items-center border-b border-slate-200 bg-white sticky top-0 z-10 py-3.5 px-4 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
        <div className="w-[120px] shrink-0 text-left font-bold text-[10px] text-slate-500 uppercase tracking-widest">
          ID
        </div>
        <div className="flex-1 text-left font-bold text-[10px] text-slate-500 uppercase tracking-widest px-4 border-l border-slate-100/50 ml-4">
          Message
        </div>
        <div className="w-[180px] shrink-0 text-left font-bold text-[10px] text-slate-500 uppercase tracking-widest px-4 border-l border-slate-100/50">
          Timestamp
        </div>
        <div className="w-[100px] shrink-0 text-right font-bold text-[10px] text-slate-500 uppercase tracking-widest px-4 border-l border-slate-100/50">
          Duration
        </div>
        <div className="w-[120px] shrink-0 text-center font-bold text-[10px] text-slate-500 uppercase tracking-widest border-l border-slate-100/50 ml-4">
          Status
        </div>
        <div className="w-[40px] shrink-0" />
      </div>

      {/* Body - Scrollable */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <div className="size-8 border-2 border-slate-200 border-t-slate-500 rounded-full animate-spin mb-4" />
            <span className="font-medium animate-pulse">
              Loading execution logs...
            </span>
          </div>
        )}
        {!isLoading && logs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <p className="text-sm font-medium">
              No logs available for this selection.
            </p>
          </div>
        )}

        {!isLoading &&
          logs.map((node) => (
            <LogRow
              key={node._id}
              node={node}
              onViewFlameChart={() => handleViewFlameChart(node)}
              onSelect={(target, root) => revealNode(target, root)}
            />
          ))}
      </div>
    </div>
  );
};

export default LogsContainer;
