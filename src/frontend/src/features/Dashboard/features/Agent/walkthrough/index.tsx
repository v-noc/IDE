import { Launcher } from "./components/Launcher";
import { TourOutline } from "./components/TourOutline";
import { useWalkthroughKeyboard } from "./hooks/useWalkthroughKeyboard";
import { useWalkthroughStore } from "./store/useWalkthroughStore";

export function WalkthroughPanel() {
  const phase = useWalkthroughStore((s) => s.phase);
  const error = useWalkthroughStore((s) => s.error);

  useWalkthroughKeyboard();

  return (
    <div className="flex h-full flex-col gap-4">
      <Launcher />

      {error ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
          {error}
        </p>
      ) : null}

      <TourOutline />

      {phase === "ready" ? (
        <p className="text-xs text-muted-foreground">
          Generation complete. Click a stop in the outline or press Play on the step
          card to begin.
        </p>
      ) : null}
    </div>
  );
}

export { StepCard } from "./components/StepCard";
export { useWalkthroughStore } from "./store/useWalkthroughStore";
