import React, { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  useFunctionLogTree,
  useCallLogTree,
} from "@/features/Dashboard/service/useLogs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import LogRow from "./LogRow";

// Row moved to dedicated component: LogRow

const LogsSection: React.FC = () => {
  const { selectedNode } = useProjectStore();
  const nodeId = selectedNode?._key || "";

  const isFunction = selectedNode?.node_type === "function";
  const isCall = selectedNode?.node_type === "call";

  const { data: fnLogs, isLoading: l1 } = useFunctionLogTree(
    isFunction ? nodeId : ""
  );
  const { data: callLogs, isLoading: l2 } = useCallLogTree(
    isCall ? nodeId : ""
  );

  const data = useMemo(
    () => (isFunction ? fnLogs : isCall ? callLogs : []),
    [isFunction, isCall, fnLogs, callLogs]
  );
  const loading = l1 || l2;

  if (!selectedNode) {
    return (
      <div className="text-sm text-muted-foreground">
        Select a function or call to see logs.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="text-sm font-medium">Logs</div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-32">Type</TableHead>
              <TableHead>Message</TableHead>
              <TableHead className="w-56">Timestamp</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell
                  colSpan={3}
                  className="text-center text-sm text-muted-foreground"
                >
                  Loading logs...
                </TableCell>
              </TableRow>
            )}
            {!loading && (!data || data.length === 0) && (
              <TableRow>
                <TableCell
                  colSpan={3}
                  className="text-center text-sm text-muted-foreground"
                >
                  No logs found.
                </TableCell>
              </TableRow>
            )}
            {!loading &&
              data &&
              data.map((node) => <LogRow key={node.id} node={node} />)}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default LogsSection;
