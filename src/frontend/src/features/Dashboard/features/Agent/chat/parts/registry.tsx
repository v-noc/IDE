import type { DecisionPart, Part, ToolPart } from "../../stream/types";
import { TextPartView } from "./TextPart";
import { ReasoningPartView } from "./ReasoningPart";
import { NodeRefChipView } from "./NodeRefChip";
import { ToolCard } from "../tool/ToolCard";

export interface PartRenderContext {
  isStreaming?: boolean;
  onFocusNode?: (part: Extract<Part, { type: "node_ref" }>) => void;
  /** Sibling decision part for the same tool_call_id, if any. */
  decisionForTool?: (toolCallId: string) => DecisionPart | null;
}

function UnknownPartChip({ type }: { type: string }) {
  return (
    <span className="rounded border border-dashed border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
      unknown part: {type}
    </span>
  );
}

export function renderPart(part: Part, ctx: PartRenderContext = {}) {
  switch (part.type) {
    case "text":
      return (
        <TextPartView part={part} isStreaming={ctx.isStreaming} />
      );
    case "reasoning":
      return (
        <ReasoningPartView part={part} isStreaming={ctx.isStreaming} />
      );
    case "node_ref":
      return (
        <NodeRefChipView part={part} onFocus={ctx.onFocusNode} />
      );
    case "decision":
      // Decisions render INSIDE their tool card, not standalone.
      return null;
    case "tool":
      return (
        <ToolCard
          part={part}
          decision={ctx.decisionForTool?.(part.tool_call_id) ?? null}
        />
      );
    default:
      return <UnknownPartChip type={(part as Part).type} />;
  }
}

export function findDecisionForTool(
  parts: Part[],
  toolCallId: string,
): DecisionPart | null {
  for (const part of parts) {
    if (part.type === "decision" && part.tool_call_id === toolCallId) {
      return part;
    }
  }
  return null;
}

export type { ToolPart };
