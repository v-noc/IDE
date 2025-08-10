import React from "react";
import { Handle, Position } from "@xyflow/react";

type DocNodeData = {
  label: string;
};

const DocNode: React.FC<
  { data: DocNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  return (
    <div
      {...props}
      className="rounded-md border bg-card text-card-foreground shadow-sm"
    >
      <div className="border-b px-3 py-2 text-sm font-medium">Docs</div>
      <div className="px-3 py-2 text-sm">{data.label}</div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default DocNode;
