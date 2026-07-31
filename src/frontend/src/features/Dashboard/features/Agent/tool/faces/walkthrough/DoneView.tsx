import { Play } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import type { DecisionPart, ToolPart } from "../../../stream/types";
import { useWalkthroughBridge } from "../../../walkthrough/hooks/useWalkthroughBridge";
import { useWalkthroughStore } from "../../../walkthrough/store/useWalkthroughStore";
import { OutlineTree } from "./OutlineTree";

interface WalkthroughDoneViewProps {
  part: ToolPart;
  decision?: DecisionPart | null;
}

export function WalkthroughDoneView({
  part,
  decision,
}: WalkthroughDoneViewProps) {
  const state = part.state;
  const doc =
    state.status === "completed" ? (state.artifact?.doc ?? "") : "";

  useWalkthroughBridge(doc);

  const [phase, playerSteps, preparing, play, exit] = useWalkthroughStore(
    useShallow((s) => [
      s.phase,
      s.playerSteps,
      s.preparing,
      s.play,
      s.exit,
    ]),
  );

  if (state.status !== "completed") return null;

  const isPlaying = phase === "playing";
  const stepCount =
    typeof state.result.steps === "number"
      ? state.result.steps
      : playerSteps.length;

  return (
    <div className="flex flex-col gap-3.5">
      <button
        type="button"
        disabled={preparing || playerSteps.length === 0}
        onClick={() => (isPlaying ? exit() : play())}
        className="inline-flex w-full items-center justify-center gap-2 rounded-agent-field border border-agent-btn-border bg-agent-btn py-2.5 text-[13px] font-semibold text-agent-on-btn transition-colors hover:bg-agent-btn-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Play className="size-3.5 fill-current" />
        {preparing
          ? "Preparing…"
          : isPlaying
            ? "Exit playback"
            : "Play walkthrough"}
      </button>
      <p className="text-center font-agent-mono text-[11px] text-agent-text-faint">
        {stepCount} steps ready
      </p>
      <OutlineTree />
      <p className="border-t border-agent-header-border pt-2.5 text-[11px] text-agent-text-faint">
        {decision?.decision === "approve" ? "approved" : "completed"} ·
        walkthrough created
      </p>
    </div>
  );
}
