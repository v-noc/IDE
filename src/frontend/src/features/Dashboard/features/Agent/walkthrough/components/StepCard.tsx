import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { GeneratingShimmer } from "./GeneratingShimmer";

interface StepCardProps {
  className?: string;
}

export function StepCard({ className }: StepCardProps) {
  const [playerSteps, cursor, session, next, prev, exit] = useWalkthroughStore(
    useShallow((state) => [
      state.playerSteps,
      state.cursor,
      state.session,
      state.next,
      state.prev,
      state.exit,
    ]),
  );

  const step = cursor >= 0 ? playerSteps[cursor] : null;
  const total = playerSteps.length;
  const position = cursor >= 0 ? cursor + 1 : 0;
  const waitingForText = step != null && step.text.trim().length === 0;
  const canPrev = cursor > 0;
  const canNext = cursor < total - 1 || session?.status === "generating";

  return (
    <div
      className={cn(
        "pointer-events-auto w-[440px] max-w-[calc(100vw-2rem)] rounded-xl border border-border bg-background p-4 text-foreground shadow-lg",
        className,
      )}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-foreground">
          {step?.title ?? "Walkthrough"}
        </p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {step?.degraded ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex items-center gap-1 text-amber-500">
                  <AlertTriangle className="h-3.5 w-3.5" />
                </span>
              </TooltipTrigger>
              <TooltipContent>Fallback text was used for this step.</TooltipContent>
            </Tooltip>
          ) : null}
          <span>
            {position} / {total || "…"}
          </span>
        </div>
      </div>

      <div className="mb-4 min-h-[3rem] text-sm leading-relaxed text-foreground">
        {waitingForText ? <GeneratingShimmer /> : <p>{step?.text ?? ""}</p>}
      </div>

      <div className="flex items-center justify-between gap-2">
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
    </div>
  );
}
