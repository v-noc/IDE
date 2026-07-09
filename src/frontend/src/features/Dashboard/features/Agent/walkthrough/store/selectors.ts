import type { WalkthroughPhase } from "../types";
import type { PlayerStep } from "../types";

export type StepAnchor =
  | { type: "node"; nodeId: string }
  | { type: "code-line"; nodeId: string; line: number };

export interface WalkthroughAnchorState {
  phase: WalkthroughPhase;
  cursor: number;
  playerSteps: PlayerStep[];
}

export function currentStepAnchor(
  s: WalkthroughAnchorState,
): StepAnchor | null {
  if (s.phase !== "playing" || s.cursor < 0) return null;
  const step = s.playerSteps[s.cursor];
  if (!step) return null;
  const hl = step.actions.find((a) => a.type === "highlight_lines");
  return hl
    ? { type: "code-line", nodeId: step.nodeId, line: hl.startLine }
    : { type: "node", nodeId: step.nodeId };
}
