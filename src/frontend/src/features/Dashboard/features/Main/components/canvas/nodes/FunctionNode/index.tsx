import React, { useState } from "react";
import { Position } from "@xyflow/react";
import CustomHandle from "../CustomHandle";
import type { FunctionNodeProps } from "../../types/node";
import { DynamicIcon } from "@/components/DynamicIcon";
import { getIcons } from "@/features/Dashboard/utils";
import { cn } from "@/lib/utils";

type FunctionNodeData = Omit<FunctionNodeProps, "id" | "children">;

const Section: React.FC<{
  title: string;
  initiallyOpen?: boolean;
  children: React.ReactNode;
}> = ({ title, initiallyOpen = true, children }) => {
  const [open, setOpen] = useState(initiallyOpen);
  return (
    <div className="border rounded-md">
      <button
        className="w-full text-left px-3 py-2 font-semibold flex items-center justify-between"
        onClick={() => setOpen((v) => !v)}
      >
        <span>{title}</span>
        <span className="text-xs text-muted-foreground">
          {open ? "Hide" : "Show"}
        </span>
      </button>
      {open ? <div className="px-3 pb-2 text-sm">{children}</div> : null}
    </div>
  );
};

const FunctionNode: React.FC<
  { data: FunctionNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  // const successColor =
  //   data.performance?.successRate && data.performance.successRate >= 0.95
  //     ? "border-green-500"
  //     : "border-red-500";
  return (
    <div
      {...props}
      className={`w-[300px] rounded-xl border-2 bg-card text-card-foreground shadow `}
    >
      <div className="border-b px-4 py-3 text-base font-semibold flex items-center gap-2">
        <DynamicIcon
          iconName={data.icon || getIcons("function")}
          className={cn("h-4 w-4 flex-shrink-0")}
          color={data.theme?.iconColor}
        />
        <span className={cn("text-sm", data.theme?.textColor)}>
          {data.name}
        </span>
      </div>

      <div className="px-4 py-3 text-sm space-y-3">
        <Section title="↓ Inputs" initiallyOpen>
          <ul className="list-disc ml-5 space-y-0.5">
            {(data.inputs ?? []).map((i) => (
              <li key={i.varname}>
                <span className="font-medium">{i.varname}</span>: {i.varType}
              </li>
            ))}
          </ul>
        </Section>
        <Section title="↑ Outputs" initiallyOpen>
          <ul className="list-disc ml-5 space-y-0.5">
            {(data.outputs ?? []).map((o) => (
              <li key={o.varname}>
                <span className="font-medium">{o.varname}</span>: {o.varType}
              </li>
            ))}
          </ul>
        </Section>
      </div>

      {data.performance ? (
        <div className="grid grid-cols-3 items-center gap-2 px-4 py-3 text-sm border-t">
          <span>⚡ {data.performance.avgTime ?? 0}ms</span>
          <span>🔄 {data.performance.runCount ?? 0}x</span>
          <span>
            ✅ {Math.round((data.performance.successRate ?? 0) * 100)}%
          </span>
        </div>
      ) : null}
      <CustomHandle type="target" position={Position.Left} size={16} />
      <CustomHandle type="source" position={Position.Right} size={16} />
    </div>
  );
};

export default FunctionNode;
