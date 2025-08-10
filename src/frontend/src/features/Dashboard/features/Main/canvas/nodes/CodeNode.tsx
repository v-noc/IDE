import React from "react";
import { Handle, Position } from "@xyflow/react";

type CodeNodeData = {
  label: string;
};

const CodeNode: React.FC<
  { data: CodeNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  return (
    <div
      {...props}
      className="rounded-md border bg-card text-card-foreground shadow-sm"
    >
      <div className="border-b px-3 py-2 text-sm font-medium">Code</div>
      <div className="px-3 py-2 text-sm">{data.label}</div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default CodeNode;
