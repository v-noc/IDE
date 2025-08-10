import React from "react";
import { Handle, Position } from "@xyflow/react";
import type { FunctionNodeProps } from "../../types/node";

type FunctionNodeData = Omit<FunctionNodeProps, "id" | "children">;

const FunctionNode: React.FC<
  { data: FunctionNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  const successColor =
    data.performance?.successRate && data.performance.successRate >= 0.95
      ? "border-green-500"
      : "border-red-500";
  return (
    <div
      {...props}
      className={`rounded-md border bg-card text-card-foreground shadow-sm ${successColor}`}
    >
      <div className="border-b px-3 py-2 text-sm font-medium">
        🔧 {data.name}
      </div>
      {data.isExpanded ? (
        <div className="px-3 py-2 text-xs space-y-2">
          <div>
            <div className="font-medium">↓ Inputs</div>
            <ul className="list-disc ml-4">
              {(data.inputs ?? []).map((i) => (
                <li key={i.name}>
                  {i.name}: {i.type}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="font-medium">↑ Outputs</div>
            <ul className="list-disc ml-4">
              {(data.outputs ?? []).map((o) => (
                <li key={o.name}>
                  {o.name}: {o.type}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
      {data.performance ? (
        <div className="flex items-center justify-between px-3 py-2 text-xs border-t">
          <span>⚡ {data.performance.avgTime ?? 0}ms</span>
          <span>🔄 {data.performance.runCount ?? 0}x</span>
          <span>
            ✅ {Math.round((data.performance.successRate ?? 0) * 100)}%
          </span>
        </div>
      ) : null}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default FunctionNode;
