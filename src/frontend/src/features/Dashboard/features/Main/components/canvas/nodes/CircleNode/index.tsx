import React from "react";
import { Position } from "@xyflow/react";
import CustomHandle from "../CustomHandle";

type CircleNodeData = {
  label: string;
  kind: "start" | "end";
};

const CircleNode: React.FC<
  { data: CircleNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  const isStart = data.kind === "start";
  return (
    <div
      {...props}
      className="w-[80px] h-[80px] rounded-full bg-card text-card-foreground shadow border flex items-center justify-center"
    >
      <span className="text-sm font-semibold text-center px-2 leading-tight">
        {data.label}
      </span>
      {isStart ? (
        <CustomHandle type="source" position={Position.Right} size={16} />
      ) : (
        <CustomHandle type="target" position={Position.Left} size={16} />
      )}
    </div>
  );
};

export default CircleNode;
