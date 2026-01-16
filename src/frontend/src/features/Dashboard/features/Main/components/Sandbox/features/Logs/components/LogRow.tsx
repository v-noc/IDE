import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CircleAlert,
  MoreHorizontal,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { type LogTreeNode } from "@/services/logs";
import { LogDetails } from "./LogDetails";
import { formatDistanceToNow } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface LogRowProps {
  node: LogTreeNode;
  depth?: number;
  onViewFlameChart?: () => void;
  onSelect?: (target: LogTreeNode, root: LogTreeNode) => void;
  rootNode?: LogTreeNode;
}

/**
 * Functional row for the Logs table with expandable details and nested children.
 */
export const LogRow: React.FC<LogRowProps> = ({ node, depth = 0, onViewFlameChart, onSelect, rootNode }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const effectiveRoot = rootNode || node;

  const filteredChildren = (node.children || []).filter(
    (c) => c.event_type !== "exit" && c.event_type !== "error"
  );

  const exitChild = (node.children || []).find((c) => c.event_type === "exit");
  const effectiveDurationMs: number | null =
    (exitChild?.duration_ms as number | null | undefined) ??
    (node.duration_ms as number | null | undefined) ??
    null;

  const formatSignificant = (value: number): string => {
    return new Intl.NumberFormat(undefined, {
      maximumSignificantDigits: 3,
      minimumSignificantDigits: 1,
    }).format(value);
  };

  const formatDurationShort = (durationMs: number | null): string => {
    if (durationMs === null || Number.isNaN(durationMs)) return "-";
    const absMs = Math.abs(durationMs);
    if (absMs >= 1000) {
      const seconds = durationMs / 1000;
      return `${formatSignificant(seconds)} s`;
    }
    if (absMs >= 0.01) {
      return `${formatSignificant(durationMs)} ms`;
    }
    if (absMs === 0) {
      return "0 ms";
    }
    const ns = durationMs * 1_000_000;
    return `${formatSignificant(ns)} ns`;
  };

  const renderStatus = () => {
    const level = (node.level_name || "").toLowerCase();

    if (level === "error" || node.error) {
      return (
        <Badge variant="destructive" className="gap-1">
          <CircleAlert className="size-3" /> Error
        </Badge>
      );
    }

    if (level === "warning" || level === "warn") {
      return (
        <Badge
          variant="secondary"
          className="bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-400/15 dark:text-amber-300 dark:border-amber-400/30 gap-1"
        >
          <AlertTriangle className="size-3" /> Warning
        </Badge>
      );
    }

    if (node.result) {
      return (
        <span className="inline-block bg-green-500/10 text-green-700 dark:text-green-400 px-2 py-0.5 rounded text-xs font-medium">
          Success
        </span>
      );
    }

    return <span className="text-muted-foreground text-xs">-</span>;
  };

  const getStatusColors = () => {
    const level = (node.level_name || "").toLowerCase();
    if (level === "error" || node.error) {
      return "bg-red-50/50 border-red-100 hover:bg-red-100/60 text-red-900";
    }
    if (level === "warning" || level === "warn") {
      return "bg-amber-50/50 border-amber-100 hover:bg-amber-100/60 text-amber-900";
    }
    return "bg-white hover:bg-slate-50 border-slate-200/60";
  };

  const statusClasses = getStatusColors();

  return (
    <div className="flex flex-col">
      {/* Main Row */}
      <div
        className={cn(
          "group flex items-center py-2.5 px-4 transition-all duration-200 border-b cursor-pointer active:opacity-70",
          statusClasses
        )}
        onClick={() => onSelect?.(node, effectiveRoot)}
      >
        <div className="w-[120px] shrink-0 flex items-center gap-2">
          <div style={{ width: `${depth * 16}px` }} className="shrink-0" />
          {filteredChildren.length > 0 ||
            node.payload ||
            node.result ||
            node.error ? (
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-5 w-5 p-0 transition-colors",
                node.level_name?.toLowerCase() === "error" || node.error
                  ? "hover:bg-red-200/50 text-red-400 group-hover:text-red-600"
                  : node.level_name?.toLowerCase() === "warning"
                    ? "hover:bg-amber-200/50 text-amber-400 group-hover:text-amber-600"
                    : "hover:bg-slate-200 text-slate-400 group-hover:text-slate-600"
              )}
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded((v) => !v);
              }}
            >
              {isExpanded ? (
                <ChevronDown className="size-3.5" />
              ) : (
                <ChevronRight className="size-3.5" />
              )}
            </Button>
          ) : (
            <div className="w-5" />
          )}
          <span className="font-mono text-[10px] opacity-60 select-all">
            {node._id?.slice(0, 8)}
          </span>
        </div>

        <div className="flex-1 px-4 min-w-0">
          <span
            className={cn(
              "text-sm truncate block font-medium transition-colors",
              node.level_name?.toLowerCase() === "error" || node.error
                ? "text-red-700"
                : node.level_name?.toLowerCase() === "warning"
                  ? "text-amber-700"
                  : "text-slate-700 group-hover:text-slate-900"
            )}
            title={node.message || ""}
          >
            {node.message || "No message"}
          </span>
        </div>

        <div className="w-[180px] shrink-0 text-xs opacity-60 font-medium whitespace-nowrap">
          {node.timestamp
            ? formatDistanceToNow(new Date(node.timestamp), { addSuffix: true })
            : "-"}
        </div>

        <div className="w-[100px] shrink-0 text-right font-mono text-xs opacity-70">
          {formatDurationShort(effectiveDurationMs)}
        </div>

        <div className="w-[120px] shrink-0 flex justify-center">
          {renderStatus()}
        </div>

        <div className="w-[40px] shrink-0 flex justify-end">
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreHorizontal className="size-4 text-slate-400" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={(e) => {
                e.stopPropagation();
                onViewFlameChart?.();
              }}>
                <Activity className="mr-2 size-4" />
                <span>View Flame Chart</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div
          className={cn(
            "border-b overflow-hidden",
            node.level_name?.toLowerCase() === "error" || node.error
              ? "bg-red-50/30 border-red-100"
              : node.level_name?.toLowerCase() === "warning"
                ? "bg-amber-50/30 border-amber-100"
                : "bg-slate-50/50 border-slate-100"
          )}
        >
          <div
            style={{ paddingLeft: `${depth * 16 + 28}px` }}
            className="py-6 pr-8"
          >
            <LogDetails
              details={{
                created_at: node.created_at,
                chain_id: node.chain_id,
                level_name: node.level_name,
                payload: node.payload,
                result: node.result,
                error: node.error,
              }}
            />
          </div>
        </div>
      )}

      {/* Recursive Children */}
      {isExpanded &&
        filteredChildren.map((child) => (
          <LogRow
            key={child._id}
            node={child}
            depth={depth + 1}
            onViewFlameChart={onViewFlameChart}
            onSelect={onSelect}
            rootNode={effectiveRoot}
          />
        ))}
    </div>
  );
};
