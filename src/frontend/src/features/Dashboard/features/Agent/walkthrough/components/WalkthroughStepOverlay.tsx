import { CodeLinePopoverLayer } from "@/features/Dashboard/features/Agent/walkthrough/components/CodeLinePopoverLayer";
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
      {phase === "playing" ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-20 z-20 flex justify-center px-4">
          <WalkthroughProgressPill />
        </div>
      ) : null}
    </>
  );
}
