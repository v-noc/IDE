import { CodeLinePopoverLayer } from "@/features/Dashboard/features/Agent/walkthrough/components/CodeLinePopoverLayer";
import { StepDialog } from "@/features/Dashboard/features/Agent/walkthrough/components/StepDialog";
import { WalkthroughProgressPill } from "@/features/Dashboard/features/Agent/walkthrough/components/WalkthroughProgressPill";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";
import { useStepExecutor } from "@/features/Dashboard/features/Agent/walkthrough/executor/useStepExecutor";

/**
 * Walkthrough overlay: line-anchored popover layer, step executor, progress pill.
 */
export function WalkthroughStepOverlay() {
  const phase = useWalkthroughStore((s) => s.phase);

  useStepExecutor();

  return (
    <>
      <CodeLinePopoverLayer />
      <StepDialog />
      {phase === "playing" ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-6 z-20 flex justify-center px-4">
          <WalkthroughProgressPill />
        </div>
      ) : null}
    </>
  );
}
