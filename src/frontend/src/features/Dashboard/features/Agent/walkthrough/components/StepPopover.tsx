import { AlertTriangle, Maximize2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { GeneratingShimmer } from "./GeneratingShimmer";
import { StepMarkdown } from "./StepMarkdown";

function stopPropagation(event: React.SyntheticEvent) {
  event.stopPropagation();
}

export function StepPopover() {
  const [playerSteps, cursor, session, setStepDialogOpen, next, prev, exit] =
    useWalkthroughStore(
      useShallow((state) => [
        state.playerSteps,
        state.cursor,
        state.session,
        state.setStepDialogOpen,
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

  const chips = useMemo(() => {
    if (!step) return [];
    const names = [step.title];
    const visit = session?.visit_list.nodes.find(
      (node) => node.order === step.visitOrder,
    );
    if (visit?.name && visit.name !== step.title) {
      names.push(visit.name);
    }
    return [...new Set(names)];
  }, [session, step]);

  return (
    <div
      data-walkthrough-popover
      className={cn(
        "agent-v2 pointer-events-auto w-[400px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-[14px] border border-agent-border-strong bg-agent-bg-tool text-agent-text shadow-[0_24px_60px_rgba(0,0,0,0.55),0_2px_8px_rgba(0,0,0,0.4)]",
      )}
      onClick={stopPropagation}
      onPointerDown={stopPropagation}
      onWheel={stopPropagation}
    >
      <div className="flex items-center gap-2.5 px-[18px] pt-3.5">
        <span
          className="size-2 shrink-0 rounded-full bg-agent-accent shadow-[0_0_8px_rgba(62,207,114,0.6)]"
          aria-hidden
        />
        <p className="min-w-0 flex-1 truncate text-base font-semibold text-agent-text">
          {step?.title ?? "Walkthrough"}
        </p>
        <div className="flex shrink-0 items-center gap-2">
          {step?.degraded ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex text-agent-warn">
                  <AlertTriangle className="size-3.5" />
                </span>
              </TooltipTrigger>
              <TooltipContent>Fallback text was used for this step.</TooltipContent>
            </Tooltip>
          ) : null}
          <button
            type="button"
            className="flex items-center justify-center rounded-agent-field p-1 text-agent-text-muted transition-colors hover:bg-agent-bg-raised hover:text-agent-text"
            aria-label="Expand step"
            onClick={(event) => {
              event.stopPropagation();
              setStepDialogOpen(true);
            }}
          >
            <Maximize2 className="size-3.5" />
          </button>
          <span className="rounded-[6px] border border-agent-border-strong bg-agent-bg-raised px-2 py-0.5 font-agent-mono text-[11.5px] text-agent-text-muted">
            {position} / {total || "…"}
          </span>
        </div>
      </div>

      <div
        className="max-h-60 overflow-y-auto overscroll-contain px-[18px] pt-3 pb-1 text-sm leading-[1.65] text-agent-text-body"
        onWheel={stopPropagation}
      >
        {waitingForText ? (
          <GeneratingShimmer />
        ) : (
          <StepMarkdown text={step?.text ?? ""} />
        )}
      </div>

      {chips.length > 0 ? (
        <div className="flex flex-wrap gap-1.5 px-[18px] py-1.5">
          {chips.map((chip) => (
            <span
              key={chip}
              className="rounded-[5px] border border-agent-accent-border bg-agent-accent-bg-subtle px-1.5 py-0.5 font-agent-mono text-[11.5px] text-agent-accent-text"
            >
              {chip}
            </span>
          ))}
        </div>
      ) : null}

      <div className="flex gap-1 px-[18px] pt-3">
        {playerSteps.map((playerStep, index) => (
          <span
            key={playerStep.id}
            className={cn(
              "h-[3px] flex-1 rounded-sm",
              index <= cursor ? "bg-agent-accent" : "bg-agent-bg-raised",
            )}
            aria-hidden
          />
        ))}
      </div>

      <div className="flex items-center px-[18px] pt-3.5 pb-4">
        <button
          type="button"
          onClick={exit}
          className="rounded-agent-field px-2.5 py-2 text-[13px] text-agent-text-muted transition-colors hover:bg-agent-bg-raised hover:text-agent-text-body"
        >
          Exit tour
        </button>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            disabled={!canPrev}
            onClick={prev}
            className="rounded-agent-field border border-agent-border-strong bg-agent-bg-inset px-4 py-2 text-[13px] font-semibold text-agent-text-body transition-colors hover:bg-agent-bg-raised disabled:cursor-not-allowed disabled:opacity-50"
          >
            Prev
          </button>
          <button
            type="button"
            disabled={!canNext && !waitingForText}
            onClick={next}
            className="rounded-agent-field border border-agent-btn-border bg-agent-btn px-4 py-2 text-[13px] font-semibold text-agent-on-btn transition-colors hover:bg-agent-btn-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
