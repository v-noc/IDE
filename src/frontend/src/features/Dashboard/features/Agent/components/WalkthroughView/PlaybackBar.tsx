import type { RefObject } from "react";
import { Pause, Play, SkipBack, SkipForward, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReplayRunner } from "../../engine/ReplayRunner";
import { useReplayStore } from "../../store/useReplayStore";
import { useShallow } from "zustand/react/shallow";

const SPEEDS = [0.5, 1, 1.5, 2] as const;

interface PlaybackBarProps {
  runnerRef: RefObject<ReplayRunner | null>;
}

export function PlaybackBar({ runnerRef }: PlaybackBarProps) {
  const [status, currentIndex, totalEvents, speed, setSpeed] = useReplayStore(
    useShallow((state) => [
      state.status,
      state.currentIndex,
      state.totalEvents,
      state.speed,
      state.setSpeed,
    ]),
  );
  const runner = runnerRef.current;

  const progress =
    totalEvents > 0 ? ((currentIndex + 1) / totalEvents) * 100 : 0;

  const handlePlayPause = () => {
    if (status === "running") {
      runner?.pause();
      return;
    }
    void runner?.play();
  };

  return (
    <div className="border-t border-border p-3 space-y-2">
      <div
        role="slider"
        aria-label="Replay progress"
        aria-valuemin={0}
        aria-valuemax={Math.max(0, totalEvents - 1)}
        aria-valuenow={currentIndex}
        className="relative h-2 w-full cursor-pointer rounded-full bg-muted"
        onClick={(event) => {
          if (totalEvents <= 1) return;
          const rect = event.currentTarget.getBoundingClientRect();
          const pct = (event.clientX - rect.left) / rect.width;
          const targetIndex = Math.round(pct * (totalEvents - 1));
          runner?.seek(targetIndex);
        }}
      >
        <div
          className="h-2 rounded-full bg-primary transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => runner?.stop()}
            className="rounded-md p-1.5 hover:bg-muted"
            aria-label="Stop"
          >
            <Square size={12} />
          </button>
          <button
            type="button"
            onClick={() => runner?.prev()}
            disabled={currentIndex <= 0 || totalEvents === 0}
            className="rounded-md p-1.5 hover:bg-muted disabled:opacity-30"
            aria-label="Previous step"
          >
            <SkipBack size={12} />
          </button>
          <button
            type="button"
            onClick={handlePlayPause}
            disabled={totalEvents === 0}
            className="rounded-md bg-primary px-3 py-1.5 text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
            aria-label={status === "running" ? "Pause" : "Play"}
          >
            {status === "running" ? <Pause size={12} /> : <Play size={12} />}
          </button>
          <button
            type="button"
            onClick={() => runner?.next()}
            disabled={totalEvents === 0 || currentIndex >= totalEvents - 1}
            className="rounded-md p-1.5 hover:bg-muted disabled:opacity-30"
            aria-label="Next step"
          >
            <SkipForward size={12} />
          </button>
        </div>

        <span className="text-muted-foreground tabular-nums">
          {totalEvents === 0 ? "0 / 0" : `${currentIndex + 1} / ${totalEvents}`}
        </span>

        <div className="flex items-center gap-1">
          {SPEEDS.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setSpeed(value);
                runner?.setSpeed(value);
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
