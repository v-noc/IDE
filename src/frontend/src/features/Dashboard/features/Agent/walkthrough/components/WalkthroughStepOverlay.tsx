import { WalkthroughProgressPill } from "@/features/Dashboard/features/Agent/walkthrough/components/WalkthroughProgressPill";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";
import { useStepExecutor } from "@/features/Dashboard/features/Agent/walkthrough/executor/useStepExecutor";

/**
 * Bottom progress pill while a tour is playing. Step text lives on the node popover.
 */
export function WalkthroughStepOverlay() {
  const phase = useWalkthroughStore((s) => s.phase);

  useStepExecutor();

  if (phase !== "playing") return null;

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-20 z-20 flex justify-center px-4">
      <WalkthroughProgressPill />
    </div>
  );
}
