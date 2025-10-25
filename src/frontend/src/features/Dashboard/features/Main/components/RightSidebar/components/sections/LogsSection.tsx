import React, { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  useFunctionLogTree,
  useCallLogTree,
} from "@/features/Dashboard/features/Main/service/useLogs";
import { Card } from "@/components/ui/card";
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
    <div className="w-full space-y-4 h-full">
      <Card className="overflow-hidden py-0 h-full">
        <div className="overflow-x-auto h-full">
          <table className="w-full text-sm max-h-full overflow-hidden">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-semibold">ID</th>

                <th className="px-4 py-3 text-left font-semibold">Message</th>
                <th className="px-4 py-3 text-left font-semibold">Timestamp</th>
                <th className="px-4 py-3 text-right font-semibold">Duration</th>
                <th className="px-4 py-3 text-left font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="h-full  overflow-y-auto">
              {loading && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    Loading logs...
                  </td>
                </tr>
              )}
              {!loading && (!data || data.length === 0) && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    No logs available
                  </td>
                </tr>
              )}
              {!loading &&
                data &&
                data.map((node) => <LogRow key={node.id} node={node} />)}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default LogsSection;
