import type { FC } from "react";
import type { WireMessagePart, WireTextPart } from "@/types/agent";
import { wirePartType } from "./partTypes";
import { TextPart } from "./parts/TextPart";
import { ToolCallPart, type ToolCallWirePart } from "./parts/ToolCallPart";
import { TaskPart, type TaskWirePart } from "./parts/task";
import {
  WalkthroughPart,
  type WalkthroughWirePart,
} from "./parts/walkthrough";
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

function isToolCallPart(p: WireMessagePart): boolean {
  return (
    typeof p === "object" &&
    p !== null &&
    String((p as { type?: unknown }).type).toLowerCase() === "tool_call" &&
    typeof (p as { tool_name?: unknown }).tool_name === "string"
  );
}

function isTaskPart(p: WireMessagePart): boolean {
  return (
    typeof p === "object" &&
    p !== null &&
    String((p as { type?: unknown }).type).toLowerCase() === "task" &&
    typeof (p as { task_id?: unknown }).task_id === "string"
  );
}

function isWalkthroughPart(p: WireMessagePart): boolean {
  if (typeof p !== "object" || p === null) return false;
  if (String((p as { type?: unknown }).type).toLowerCase() !== "walkthrough") {
    return false;
  }
  const w = (p as { walkthrough?: unknown }).walkthrough;
  return (
    typeof w === "object" &&
    w !== null &&
    typeof (w as { meta?: unknown }).meta === "object" &&
    (w as { meta: object }).meta !== null &&
    typeof (w as { meta: { id?: unknown } }).meta.id === "string" &&
    Array.isArray((w as { steps?: unknown }).steps)
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
    isToolCallPart(part) ? (
      <ToolCallPart part={part as unknown as ToolCallWirePart} />
    ) : (
      <UnknownPart part={part} />
    ),
  task: ({ part }) =>
    isTaskPart(part) ? (
      <TaskPart part={part as unknown as TaskWirePart} />
    ) : (
      <UnknownPart part={part} />
    ),
  walkthrough: ({ part }) =>
    isWalkthroughPart(part) ? (
      <WalkthroughPart part={part as unknown as WalkthroughWirePart} />
    ) : (
      <UnknownPart part={part} />
    ),
};

export function PartRenderer(props: PartRendererProps) {
  const t = wirePartType(props.part);
  const C = REGISTRY[t];
  if (!C) {
    return <UnknownPart part={props.part} />;
  }
  return <C {...props} />;
}
