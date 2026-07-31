import "../../theme/tokens.css";
import { CodeLinePopoverLayer } from "./CodeLinePopoverLayer";
import { StepDialog } from "./StepDialog";
import { WalkthroughProgressPill } from "./WalkthroughProgressPill";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { useStepExecutor } from "../executor/useStepExecutor";

/**
 * Walkthrough overlay: line-anchored popover layer, step executor, progress pill.
 */
export function WalkthroughStepOverlay() {
  const phase = useWalkthroughStore((s) => s.phase);

  useStepExecutor();

  return (
    <div className="agent-v2">
      <CodeLinePopoverLayer />
      <StepDialog />
      {phase === "playing" ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-5 z-20 flex justify-center px-4">
          <WalkthroughProgressPill />
        </div>
      ) : null}
    </div>
  );
}
