import type { DecisionPart, Part } from "../../stream/types";
import { ToolCard } from "../../tool/ToolCard";
import { NodeRefChip } from "./NodeRefChip";
import { ReasoningPartView } from "./ReasoningPart";
import { TextPartView } from "./TextPart";

export interface PartRenderContext {
  isStreaming?: boolean;
  onFocusNode?: (part: Extract<Part, { type: "node_ref" }>) => void;
  decisionForTool?: (toolCallId: string) => DecisionPart | null;
}

function UnknownPartChip({ type }: { type: string }) {
  return (
    <span className="rounded-agent-field border border-dashed border-agent-border px-1.5 py-0.5 font-agent-mono text-[10px] text-agent-text-muted">
      unknown part: {type}
    </span>
  );
}

export function renderPart(part: Part, ctx: PartRenderContext = {}) {
  switch (part.type) {
    case "text":
      return <TextPartView part={part} isStreaming={ctx.isStreaming} />;
    case "reasoning":
      return (
        <ReasoningPartView part={part} isStreaming={ctx.isStreaming} />
      );
    case "node_ref":
      return <NodeRefChip part={part} onFocus={ctx.onFocusNode} />;
    case "decision":
      return null;
    case "tool":
      return (
        <ToolCard
          part={part}
          decision={ctx.decisionForTool?.(part.tool_call_id) ?? null}
        />
      );
    default: {
      const unknown = part as Part;
      return <UnknownPartChip type={unknown.type} />;
    }
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
