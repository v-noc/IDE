import React from "react";
import { LogRow } from "./components/LogRow";
import { useLogsState } from "./hooks/useLogsState";

/**
 * Logs Feature.
 * Selection-based log viewer for execution traces.
 */
export const LogsContainer: React.FC = () => {
  const { logs, isLoading, hasSelection } = useLogsState();

  if (!hasSelection) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8 text-center text-sm text-muted-foreground bg-white/50 rounded-md border border-dashed">
        Select a function or call in the workspace to view execution logs.
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
          logs.map((node) => <LogRow key={node._id} node={node} />)}
      </div>
    </div>
  );
};

export default LogsContainer;
