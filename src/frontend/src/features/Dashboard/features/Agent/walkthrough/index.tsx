import { Launcher } from "./components/Launcher";
import { PlayControls } from "./components/PlayControls";
import { TourOutline } from "./components/TourOutline";
import { useWalkthroughKeyboard } from "./hooks/useWalkthroughKeyboard";
import { useWalkthroughStore } from "./store/useWalkthroughStore";

export function WalkthroughPanel() {
  const error = useWalkthroughStore((s) => s.error);

  useWalkthroughKeyboard();

  return (
    <div className="flex h-full flex-col gap-4">
      <Launcher />

      <PlayControls />

      {error ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
          {error}
        </p>
      ) : null}

      <TourOutline />
    </div>
  );
}

export { StepCard } from "./components/StepCard";
export { useWalkthroughStore } from "./store/useWalkthroughStore";
