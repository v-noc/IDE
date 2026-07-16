import type { ComponentType } from "react";
import type { DecisionPart, ToolEstimate, ToolPart } from "../../stream/types";
import { WalkthroughConfigForm } from "./walkthrough/ConfigForm";
import { WalkthroughDoneView } from "./walkthrough/DoneView";

export interface ToolConfigFormProps {
  part: ToolPart;
  estimate: ToolEstimate;
  input: Record<string, unknown>;
}

export interface ToolDoneViewProps {
  part: ToolPart;
  decision?: DecisionPart | null;
}

export interface ToolFace {
  ConfigForm: ComponentType<ToolConfigFormProps>;
  DoneView: ComponentType<ToolDoneViewProps>;
}

function GenericDoneView({ part }: ToolDoneViewProps) {
  const state = part.state;
  if (state.status !== "completed") return null;
  return (
    <p className="text-[12px] text-agent-text-muted">
      {typeof state.result.message === "string"
        ? state.result.message
        : "Tool completed."}
    </p>
  );
}

export const TOOL_FACES: Record<string, ToolFace> = {
  walkthrough: {
    ConfigForm: WalkthroughConfigForm,
    DoneView: WalkthroughDoneView,
  },
};

export function getToolFace(toolId: string): ToolFace {
  return (
    TOOL_FACES[toolId] ?? {
      ConfigForm: () => (
        <p className="text-xs text-agent-text-muted">
          Confirmation is not available for this tool yet.
        </p>
      ),
      DoneView: GenericDoneView,
    }
  );
}
