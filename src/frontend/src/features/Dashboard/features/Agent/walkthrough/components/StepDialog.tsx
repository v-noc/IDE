import "../../theme/tokens.css";

import { AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { GeneratingShimmer } from "./GeneratingShimmer";
import { StepMarkdown } from "./StepMarkdown";

const DIALOG_W = "min(90vw, 48rem)";
const DIALOG_H = "min(80vh, 36rem)";

export function StepDialog() {
  const [
    phase,
    playerSteps,
    cursor,
    session,
    stepDialogOpen,
    setStepDialogOpen,
    next,
    prev,
    exit,
  ] = useWalkthroughStore(
    useShallow((state) => [
      state.phase,
      state.playerSteps,
      state.cursor,
      state.session,
      state.stepDialogOpen,
      state.setStepDialogOpen,
      state.next,
      state.prev,
      state.exit,
    ]),
  );

  if (phase !== "playing") {
    return null;
  }

  const step = cursor >= 0 ? playerSteps[cursor] : null;
  const total = playerSteps.length;
  const position = cursor >= 0 ? cursor + 1 : 0;
  const waitingForText = step != null && step.text.trim().length === 0;
  const canPrev = cursor > 0;
  const canNext = cursor < total - 1 || session?.status === "generating";

  return (
    <Dialog
      open={stepDialogOpen}
      onOpenChange={(open) => {
        if (phase !== "playing") {
          setStepDialogOpen(false);
          return;
        }
        setStepDialogOpen(open);
      }}
    >
      <DialogContent
        className="agent-v2 flex max-w-none flex-col gap-0 overflow-hidden border-agent-border-strong bg-agent-bg-tool p-0 text-agent-text sm:max-w-none"
        style={{ width: DIALOG_W, height: DIALOG_H }}
      >
        <DialogHeader className="shrink-0 space-y-0 border-b border-agent-border px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <DialogTitle className="truncate text-base font-semibold text-agent-text">
              {step?.title ?? "Walkthrough"}
            </DialogTitle>
            <div className="flex shrink-0 items-center gap-2 font-agent-mono text-xs text-agent-text-muted">
              {step?.degraded ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="inline-flex text-agent-warn">
                      <AlertTriangle className="size-3.5" />
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    Fallback text was used for this step.
                  </TooltipContent>
                </Tooltip>
              ) : null}
              <span>
                {position} / {total || "…"}
              </span>
            </div>
          </div>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-4 text-sm leading-relaxed text-agent-text-body">
          {waitingForText ? (
            <GeneratingShimmer />
          ) : (
            <StepMarkdown text={step?.text ?? ""} />
          )}
        </div>

        <div className="flex shrink-0 items-center justify-between gap-2 border-t border-agent-border px-5 py-4">
          <button
            type="button"
            onClick={exit}
            className="rounded-agent-field px-2.5 py-2 text-sm text-agent-text-muted hover:bg-agent-bg-raised hover:text-agent-text-body"
          >
            Exit tour
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={!canPrev}
              onClick={prev}
              className="rounded-agent-field border border-agent-border-strong bg-agent-bg-inset px-4 py-2 text-sm font-semibold text-agent-text-body disabled:opacity-50"
            >
              Prev
            </button>
            <button
              type="button"
              disabled={!canNext && !waitingForText}
              onClick={next}
              className="rounded-agent-field border border-agent-btn-border bg-agent-btn px-4 py-2 text-sm font-semibold text-agent-on-btn hover:bg-agent-btn-hover disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
