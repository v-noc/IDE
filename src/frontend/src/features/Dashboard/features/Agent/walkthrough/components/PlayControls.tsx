import { Button } from "@/components/ui/button";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

export function PlayControls() {
  const [phase, playerSteps, cursor, session, preparing, play, exit] =
    useWalkthroughStore(
    useShallow((state) => [
      state.phase,
      state.playerSteps,
      state.cursor,
      state.session,
      state.preparing,
      state.play,
      state.exit,
    ]),
  );

  if (playerSteps.length === 0) return null;

  const isPlaying = phase === "playing";
  const resumeStep = cursor >= 0 ? cursor + 1 : 1;

  return (
    <section className="space-y-2 rounded-md border border-border bg-muted/20 p-3">
      {isPlaying ? (
        <Button type="button" variant="outline" size="sm" className="w-full" onClick={exit}>
          ⏸ Exit playback
        </Button>
      ) : (
        <Button
          type="button"
          size="sm"
          className="w-full"
          disabled={preparing}
          onClick={play}
        >
          {preparing
            ? "Preparing…"
            : cursor > 0
              ? `▶ Resume (step ${resumeStep})`
              : "▶ Play walkthrough"}
        </Button>
      )}
      <p className="text-[11px] text-muted-foreground">
        {playerSteps.length} steps ready
        {session?.status === "generating" ? " · still generating…" : ""}
      </p>
    </section>
  );
}
