import React from "react";
import { Handle, Position } from "@xyflow/react";
import type { ClassNodeProps } from "../../types/node";

type ClassNodeData = Omit<ClassNodeProps, "id">;

const ClassNode: React.FC<
  { data: ClassNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  return (
    <div
      {...props}
      className="rounded-md border bg-card text-card-foreground shadow-sm"
    >
      <div className="border-b px-3 py-2 text-sm font-medium">
        🏛️ {data.name}
      </div>
      {data.isExpanded ? (
        <div className="px-3 py-2 text-xs space-y-2">
          <div>
            <div className="font-medium">📋 Fields</div>
            <ul className="list-disc ml-4">
              {(data.fields ?? []).map((f) => (
                <li key={f.name}>
                  {f.name}: {f.type}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="font-medium">🔧 Methods</div>
            <ul className="list-disc ml-4">
              {(data.methods ?? []).map((m) => (
                <li key={m.name}>
                  {m.name}
                  {m.returnType ? ` → ${m.returnType}` : ""}
                </li>
              ))}
            </ul>
          </div>
          <div className="text-muted-foreground">
            📦 From: {data.sourceFile}
          </div>
        </div>
      ) : null}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default ClassNode;
