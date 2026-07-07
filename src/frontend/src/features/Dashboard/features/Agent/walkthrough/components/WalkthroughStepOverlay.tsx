import { StepCard } from "@/features/Dashboard/features/Agent/walkthrough";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";
import { useStepExecutor } from "@/features/Dashboard/features/Agent/walkthrough/executor/useStepExecutor";

/**
 * Fixed bottom-center overlay for the walkthrough step card.
 * Sibling of the canvas so it survives node mount/unmount during the tour.
 */
export function WalkthroughStepOverlay() {
  const phase = useWalkthroughStore((s) => s.phase);
  const show =
    phase === "playing" || phase === "generating" || phase === "ready";

  useStepExecutor();

  if (!show) return null;

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-4 z-20 flex justify-center px-4">
      <StepCard />
    </div>
  );
}
