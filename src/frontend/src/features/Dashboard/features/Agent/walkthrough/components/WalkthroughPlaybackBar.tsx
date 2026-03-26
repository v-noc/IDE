import {
  PanelBottom,
  PanelRight,
  Pause,
  Play,
  SkipBack,
  SkipForward,
  Square,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useShallow } from "zustand/react/shallow";
import { useAgentOverlayStore } from "../../store/useAgentOverlayStore";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

const SPEEDS = [0.5, 1, 1.5, 2] as const;

export type WalkthroughPlaybackPlacement = "sidebar" | "floating";

interface WalkthroughPlaybackBarProps {
  placement?: WalkthroughPlaybackPlacement;
}

export function WalkthroughPlaybackBar({
  placement = "sidebar",
}: WalkthroughPlaybackBarProps) {
  const [
    status,
    currentStepIndex,
    totalSteps,
    speed,
    setSpeed,
    timeline,
    elapsedMs,
    controls,
    setPlaybackDetached,
  ] = useWalkthroughStore(
    useShallow((s) => [
      s.status,
      s.currentStepIndex,
      s.totalSteps,
      s.speed,
      s.setSpeed,
      s.timeline,
      s.elapsedMs,
      s.controls,
      s.setPlaybackDetached,
    ]),
  );

  const setAgentOpen = useAgentOverlayStore((s) => s.setOpen);

  const totalMs = timeline?.totalDuration ?? 0;
  const progressPct =
    totalMs > 0 ? Math.min(100, (elapsedMs / totalMs) * 100) : 0;

  const handlePlayPause = () => {
    if (!controls) return;
    if (status === "running") {
      controls.pause();
      return;
    }
    void controls.play();
  };

  if (!controls || totalSteps === 0) {
    return (
      <div className="rounded-md border border-border bg-muted/30 px-3 py-2 text-[11px] text-muted-foreground">
        Walkthrough: load a tour via{" "}
        <code className="rounded bg-muted px-1">controls.load()</code> (devtools)
        or your agent flow.
      </div>
    );
  }

  const shellClass =
    placement === "floating"
      ? "space-y-2 rounded-lg border border-border bg-background/95 p-3 shadow-lg backdrop-blur-sm"
      : "space-y-2 rounded-md border border-border bg-muted/20 p-3";

  return (
    <div className={shellClass}>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        Walkthrough
      </p>
      <div
        role="slider"
        aria-label="Walkthrough progress"
        aria-valuemin={0}
        aria-valuemax={totalMs}
        aria-valuenow={Math.round(elapsedMs)}
        className="relative h-2 w-full cursor-pointer rounded-full bg-muted"
        onClick={(event) => {
          if (totalMs <= 0) return;
          const rect = event.currentTarget.getBoundingClientRect();
          const pct = (event.clientX - rect.left) / rect.width;
          void controls.seekToTime(pct * totalMs);
        }}
      >
        <div
          className="h-2 rounded-full bg-primary transition-[width]"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => controls.stop()}
            className="rounded-md p-1.5 hover:bg-muted"
            aria-label="Stop"
          >
            <Square size={12} />
          </button>
          <button
            type="button"
            onClick={() => void controls.prev()}
            disabled={currentStepIndex <= 0}
            className="rounded-md p-1.5 hover:bg-muted disabled:opacity-30"
            aria-label="Previous step"
          >
            <SkipBack size={12} />
          </button>
          <button
            type="button"
            onClick={handlePlayPause}
            className="rounded-md bg-primary px-3 py-1.5 text-primary-foreground hover:bg-primary/90"
            aria-label={status === "running" ? "Pause" : "Play"}
          >
            {status === "running" ? <Pause size={12} /> : <Play size={12} />}
          </button>
          <button
            type="button"
            onClick={() => void controls.next()}
            disabled={currentStepIndex >= totalSteps - 1}
            className="rounded-md p-1.5 hover:bg-muted disabled:opacity-30"
            aria-label="Next step"
          >
            <SkipForward size={12} />
          </button>
        </div>

        <span className="text-muted-foreground tabular-nums">
          {currentStepIndex + 1} / {totalSteps} · {status}
        </span>

        <div className="flex items-center gap-1">
          {SPEEDS.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setSpeed(value);
                controls.setSpeed(value);
              }}
              className={cn(
                "rounded px-1.5 py-0.5",
                speed === value
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {value}x
            </button>
          ))}
          {placement === "sidebar" ? (
            <button
              type="button"
              onClick={() => {
                setPlaybackDetached(true);
                setAgentOpen(false);
              }}
              className="ml-0.5 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label="Detach walkthrough bar to canvas"
              title="Detach to canvas"
            >
              <PanelBottom size={12} />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                setPlaybackDetached(false);
                setAgentOpen(true);
              }}
              className="ml-0.5 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label="Attach walkthrough bar to sidebar"
              title="Attach to sidebar"
            >
              <PanelRight size={12} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
