import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

export function WalkthroughProgressPill() {
  const [playerSteps, cursor, exit] = useWalkthroughStore(
    useShallow((state) => [state.playerSteps, state.cursor, state.exit]),
  );

  const step = cursor >= 0 ? playerSteps[cursor] : null;
  const position = cursor >= 0 ? cursor + 1 : 0;
  const total = playerSteps.length;

  return (
    <div className="agent-v2 pointer-events-auto flex items-center gap-3 rounded-agent-pill border border-agent-border-strong bg-[rgba(24,26,30,0.92)] px-4 py-2 shadow-[0_8px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
      <span
        className="agent-status-dot--pulse size-[7px] shrink-0 rounded-full bg-agent-accent"
        aria-hidden
      />
      <span className="text-[13px] font-semibold text-agent-text">
        {step?.title ?? "Walkthrough"}
      </span>
      <span className="font-agent-mono text-[11px] text-agent-text-muted">
        {position} / {total || "…"}
      </span>
      <button
        type="button"
        onClick={exit}
        className="rounded-agent-pill border border-agent-border-strong bg-agent-bg-raised px-3 py-1 text-xs text-agent-text-muted transition-colors hover:text-agent-text"
      >
        Exit
      </button>
    </div>
  );
}
