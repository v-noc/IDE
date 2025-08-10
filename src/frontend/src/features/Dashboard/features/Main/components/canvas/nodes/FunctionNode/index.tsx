import React, { useState } from "react";
import type { FunctionNodeProps } from "../../types/node";
import { getIcons } from "@/features/Dashboard/utils";
import BaseNode from "../BaseNode";

type FunctionNodeData = FunctionNodeProps;

const Section: React.FC<{
  title: string;
  initiallyOpen?: boolean;
  children: React.ReactNode;
  textColor?: string;
}> = ({ title, initiallyOpen = true, children, textColor }) => {
  const [open, setOpen] = useState(initiallyOpen);
  return (
    <div className="border rounded-md">
      <button
        className="w-full text-left px-3 py-2 font-semibold flex items-center justify-between"
        onClick={() => setOpen((v) => !v)}
      >
        <span style={{ color: textColor }}>{title}</span>
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
  return (
    <BaseNode
      id={data.id}
      iconName={data.icon || getIcons("function")}
      title={data.name}
      isSelected={data.isSelected ?? false}
      type="function"
      theme={data.theme}
      isExpandable={data.isExpandable ?? false}
      {...props}
    >
      <div className="text-sm space-y-3">
        <Section
          title="↓ Inputs"
          initiallyOpen
          textColor={data.theme?.textColor}
        >
          <ul
            className="list-disc ml-5 space-y-0.5"
            style={{ color: data.theme?.textColor }}
          >
            {(data.inputs ?? []).map((i) => (
              <li key={i.varname}>
                <span
                  className="font-medium"
                  style={{ color: data.theme?.textColor }}
                >
                  {i.varname}
                </span>
                : {i.varType}
              </li>
            ))}
          </ul>
        </Section>
        <Section
          title="↑ Outputs"
          initiallyOpen
          textColor={data.theme?.textColor}
        >
          <ul
            className="list-disc ml-5 space-y-0.5"
            style={{ color: data.theme?.textColor }}
          >
            {(data.outputs ?? []).map((o) => (
              <li key={o.varname}>
                <span
                  className="font-medium"
                  style={{ color: data.theme?.textColor }}
                >
                  {o.varname}
                </span>
                : {o.varType}
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
    </BaseNode>
  );
};

export default FunctionNode;
