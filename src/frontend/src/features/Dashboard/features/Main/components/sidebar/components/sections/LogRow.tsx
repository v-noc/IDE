import React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { type LogTreeNode } from "@/features/Dashboard/service/useLogs";
import LogDetails, { type LogDetailsData } from "./LogDetails";
import { TableRow, TableCell } from "@/components/ui/table";

export type RowProps = {
  node: LogTreeNode;
  depth?: number;
};

function buildDetails(node: LogTreeNode): LogDetailsData {
  const exitChild = node.children?.find((c) => c.event_type === "exit");
  const errorChild = node.children?.find((c) => c.event_type === "error");
  return {
    id: node.id,
    timestamp: node.timestamp,
    duration_ms: node.duration_ms ?? exitChild?.duration_ms ?? null,
    chain_id: node.chain_id ?? exitChild?.chain_id ?? null,
    payload: node.payload ?? null,
    result: node.result ?? exitChild?.result ?? null,
    error: node.error ?? errorChild?.error ?? null,
  };
}

const LogRow: React.FC<RowProps> = ({ node, depth = 0 }) => {
  const [open, setOpen] = React.useState(false);
  const filteredChildren = (node.children || []).filter(
    (c) => c.event_type !== "exit" && c.event_type !== "error"
  );

  return (
    <>
      <TableRow className={open ? "bg-muted/30" : undefined}>
        <TableCell>
          <div
            className="flex items-center gap-1"
            style={{ paddingLeft: (depth ?? 0) * 12 }}
          >
            <button className="p-1" onClick={() => setOpen((v) => !v)}>
              {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            <span className="font-mono text-xs opacity-70">
              {node.event_type}
            </span>
          </div>
        </TableCell>
        <TableCell
          className="font-medium truncate max-w-[380px]"
          title={node.message}
        >
          {node.message}
        </TableCell>
        <TableCell className="text-xs opacity-70">
          {new Date(node.timestamp).toLocaleString()}
        </TableCell>
      </TableRow>

      {open &&
        filteredChildren.map((child) => (
          <LogRow key={child.id} node={child} depth={(depth ?? 0) + 1} />
        ))}

      {open && (
        <TableRow className="bg-muted/20">
          <TableCell colSpan={3}>
            <LogDetails details={buildDetails(node)} />
          </TableCell>
        </TableRow>
      )}
    </>
  );
};

export default LogRow;
