import type { FC } from "react";
import type { WireMessagePart, WireTextPart } from "@/types/agent";
import { wirePartType } from "./partTypes";
import { TextPart } from "./parts/TextPart";
import { ToolCallPart, type ToolCallWirePart } from "./parts/ToolCallPart";
import { TaskPart, type TaskWirePart } from "./parts/task";
import { UnknownPart } from "./parts/UnknownPart";

export interface PartRendererProps {
  part: WireMessagePart;
  role: string;
  streaming?: boolean;
}

function isTextPart(p: WireMessagePart): p is WireTextPart {
  return (
    typeof p === "object" &&
    p !== null &&
    typeof (p as WireTextPart).text === "string" &&
    String((p as { type?: unknown }).type).toLowerCase() === "text"
  );
}

function isToolCallPart(p: WireMessagePart): p is ToolCallWirePart {
  return (
    typeof p === "object" &&
    p !== null &&
    String((p as { type?: unknown }).type).toLowerCase() === "tool_call" &&
    typeof (p as ToolCallWirePart).tool_name === "string"
  );
}

function isTaskPart(p: WireMessagePart): p is TaskWirePart {
  return (
    typeof p === "object" &&
    p !== null &&
    String((p as { type?: unknown }).type).toLowerCase() === "task" &&
    typeof (p as TaskWirePart).task_id === "string"
  );
}

const REGISTRY: Record<string, FC<PartRendererProps>> = {
  text: ({ part, role, streaming }) =>
    isTextPart(part) ? (
      <TextPart part={part} role={role} streaming={streaming} />
    ) : (
      <UnknownPart part={part} />
    ),
  tool_call: ({ part }) =>
    isToolCallPart(part) ? <ToolCallPart part={part} /> : <UnknownPart part={part} />,
  task: ({ part }) => (isTaskPart(part) ? <TaskPart part={part} /> : <UnknownPart part={part} />),
};

export function PartRenderer(props: PartRendererProps) {
  const t = wirePartType(props.part);
  const C = REGISTRY[t];
  if (!C) {
    return <UnknownPart part={props.part} />;
  }
  return <C {...props} />;
}
