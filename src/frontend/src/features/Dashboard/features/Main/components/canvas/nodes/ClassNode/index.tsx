import React, { useState } from "react";
import type { ClassNodeProps } from "../../types/node";
import { getIcons } from "@/features/Dashboard/utils";
import { Separator } from "@/components/ui/separator";
import BaseNode from "../BaseNode";
import { DynamicIcon } from "@/components/DynamicIcon";

type ClassNodeData = ClassNodeProps;

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

const ClassNode: React.FC<
  { data: ClassNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  return (
    <BaseNode
      id={data.id}
      iconName={data.icon || getIcons("class")}
      title={data.name}
      theme={data.theme}
      isSelected={data.isSelected ?? false}
      type="class"
      isExpandable={data.isExpandable ?? false}
      {...props}
    >
      <div className="space-y-3">
        <Section
          title="📋 Fields"
          initiallyOpen
          textColor={data.theme?.textColor}
        >
          <Separator />
          <ul
            className="list-disc ml-5 space-y-0.5"
            style={{ color: data.theme?.textColor }}
          >
            {(data.fields ?? []).map((f) => (
              <li key={f.varname}>
                <span
                  className="font-medium"
                  style={{ color: data.theme?.textColor }}
                >
                  {f.varname}
                </span>
                : {f.varType}
              </li>
            ))}
          </ul>
        </Section>
        <Section
          title="🔧 Methods"
          initiallyOpen
          textColor={data.theme?.textColor}
        >
          <Separator />
          <ul
            className="ml-1 space-y-1"
            style={{ color: data.theme?.textColor }}
          >
            {(data.methods ?? []).map((m) => (
              <li key={m.name}>
                <button
                  className="w-full text-left px-2 py-1 rounded hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Hook for future: expand method as separate flow
                  }}
                >
                  <DynamicIcon
                    iconName={m.icon || getIcons("function")}
                    className="w-4 h-4"
                  />
                  <span
                    className="text-sm"
                    style={{ color: data.theme?.textColor }}
                  >
                    {m.name}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Section>
        <div
          className="text-xs text-muted-foreground px-1"
          style={{ color: data.theme?.textColor }}
        >
          📦 From: {data.sourceFile}
        </div>
      </div>
    </BaseNode>
  );
};

export default ClassNode;
