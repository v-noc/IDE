import React, { useState } from "react";
import { Handle, Position } from "@xyflow/react";
import type { ClassNodeProps } from "../../types/node";
import { DynamicIcon } from "@/components/DynamicIcon";
import { getIcons } from "@/features/Dashboard/utils";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

type ClassNodeData = Omit<ClassNodeProps, "id">;

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

const ClassNode: React.FC<
  { data: ClassNodeData } & React.ComponentProps<"div">
> = ({ data, ...props }) => {
  return (
    <div
      {...props}
      className="w-[300px] rounded-xl border bg-card text-card-foreground shadow"
    >
      <div className="border-b px-4 py-3 text-base font-semibold flex items-center gap-2">
        <DynamicIcon
          iconName={data.icon || getIcons("class")}
          className={cn("h-4 w-4 flex-shrink-0")}
          color={data.theme?.iconColor}
        />
        <span className={cn("text-sm", data.theme?.textColor)}>
          {data.name}
        </span>
      </div>

      <div className="px-4 py-3 space-y-3">
        <Section title="📋 Fields" initiallyOpen>
          <Separator />
          <ul className="list-disc ml-5 space-y-0.5">
            {(data.fields ?? []).map((f) => (
              <li key={f.varname}>
                <span className="font-medium">{f.varname}</span>: {f.varType}
              </li>
            ))}
          </ul>
        </Section>
        <Section title="🔧 Methods" initiallyOpen>
          <Separator />
          <ul className="ml-1 space-y-1">
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
                    className={cn("h-4 w-4 flex-shrink-0")}
                    color={m.theme?.iconColor}
                  />
                  <span className={cn("text-sm", m.theme?.textColor)}>
                    {m.name}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Section>
        <div className="text-xs text-muted-foreground px-1">
          📦 From: {data.sourceFile}
        </div>
      </div>

      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default ClassNode;
