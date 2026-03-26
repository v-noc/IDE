import { Pause, Play, SkipBack, SkipForward, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

const SPEEDS = [0.5, 1, 1.5, 2] as const;

export function WalkthroughPlaybackBar() {
  const [
    status,
    currentStepIndex,
    totalSteps,
    speed,
    setSpeed,
    timeline,
    elapsedMs,
    controls,
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
    ]),
  );

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

  return (
    <div className="space-y-2 rounded-md border border-border bg-muted/20 p-3">
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
        </div>
      </div>
    </div>
  );
}
