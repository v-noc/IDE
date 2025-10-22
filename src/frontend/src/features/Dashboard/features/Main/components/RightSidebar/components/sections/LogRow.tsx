import React, { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { type LogTreeNode } from "@/features/Dashboard/features/Main/service/useLogs";
import LogDetails from "./LogDetails";
import { TableRow, TableCell } from "@/components/ui/table";

export type RowProps = {
  node: LogTreeNode;
  depth?: number;
};

// Note: details are shown from the node directly in this UI version.

const LogRow: React.FC<RowProps> = ({ node, depth = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(false);
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
    if (absMs >= 1) {
      return `${formatSignificant(durationMs)} ms`;
    }
    if (absMs === 0) {
      return "0 ms";
    }
    const ns = durationMs * 1_000_000;
    return `${formatSignificant(ns)} ns`;
  };

  return (
    <>
      <TableRow className="border-b border-border hover:bg-muted/50 transition-colors">
        <TableCell>
          <div
            style={{ paddingLeft: `${(depth ?? 0) * 24}px` }}
            className="flex items-center gap-2"
          >
            {filteredChildren.length > 0 ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => setIsExpanded((v) => !v)}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            ) : (
              <div className="h-6 w-6" />
            )}
            <span className="font-mono text-sm text-muted-foreground">
              {node.id}
            </span>
          </div>
        </TableCell>
        <TableCell>
          <span className="inline-block bg-primary/10 text-primary px-2 py-1 rounded text-xs font-medium">
            {node.event_type}
          </span>
        </TableCell>
        <TableCell className="max-w-xs truncate text-sm" title={node.message}>
          {node.message}
        </TableCell>
        <TableCell className="text-sm text-muted-foreground">
          {new Date(node.timestamp).toLocaleString()}
        </TableCell>
        <TableCell className="text-sm text-right">
          {formatDurationShort(effectiveDurationMs)}
        </TableCell>
        <TableCell>
          {node.error ? (
            <span className="inline-block bg-destructive/10 text-destructive px-2 py-1 rounded text-xs font-medium">
              Error
            </span>
          ) : node.result ? (
            <span className="inline-block bg-green-500/10 text-green-700 dark:text-green-400 px-2 py-1 rounded text-xs font-medium">
              Success
            </span>
          ) : (
            <span className="text-muted-foreground text-xs">-</span>
          )}
        </TableCell>
      </TableRow>

      {isExpanded && (
        <TableRow className="border-b border-border bg-muted/30">
          <TableCell colSpan={6}>
            <div
              style={{ paddingLeft: `${(depth ?? 0) * 24 + 40}px` }}
              className="space-y-4"
            >
              <LogDetails
                details={{
                  created_at: node.created_at,
                  chain_id: node.chain_id,
                  payload: node.payload,
                  result: node.result,
                  error: node.error,
                }}
              />
            </div>
          </TableCell>
        </TableRow>
      )}

      {isExpanded &&
        filteredChildren.map((child) => (
          <LogRow key={child.id} node={child} depth={(depth ?? 0) + 1} />
        ))}
    </>
  );
};

export default LogRow;
