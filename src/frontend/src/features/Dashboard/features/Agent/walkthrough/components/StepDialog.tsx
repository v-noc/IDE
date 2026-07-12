import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
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

/** Fixed dialog size — matches the canvas code expand dialog feel. */
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
        className="flex max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none"
        style={{ width: DIALOG_W, height: DIALOG_H }}
      >
        <DialogHeader className="shrink-0 space-y-0 border-b border-border px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <DialogTitle className="truncate text-base font-medium">
              {step?.title ?? "Walkthrough"}
            </DialogTitle>
            <div className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
              {step?.degraded ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="inline-flex items-center gap-1 text-amber-500">
                      <AlertTriangle className="h-3.5 w-3.5" />
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

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-4 text-sm leading-relaxed">
          {waitingForText ? (
            <GeneratingShimmer />
          ) : (
            <StepMarkdown text={step?.text ?? ""} />
          )}
        </div>

        <div className="flex shrink-0 items-center justify-between gap-2 border-t border-border px-5 py-4">
          <Button type="button" variant="ghost" size="sm" onClick={exit}>
            Exit
          </Button>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!canPrev}
              onClick={prev}
            >
              Prev
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={!canNext && !waitingForText}
              onClick={next}
            >
              Next
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
