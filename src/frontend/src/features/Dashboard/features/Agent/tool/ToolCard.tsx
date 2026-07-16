import { useEffect, useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import type { DecisionPart, ToolPart, ToolState } from "../stream/types";
import { useAgentRunStore } from "../store/useAgentRunStore";
import { getToolInfo } from "../tools/registry";
import { getToolFace } from "./faces/registry";
import { ToolBadge, type ToolBadgeStatus } from "./ToolBadge";
import { ToolProgress } from "./ToolProgress";

function isCancelled(
  state: ToolState,
  decision?: DecisionPart | null,
): boolean {
  if (decision?.decision === "cancel") return true;
  return state.status === "error" && state.error.toLowerCase().includes("declined");
}

function badgeStatus(
  state: ToolState,
  decision?: DecisionPart | null,
): ToolBadgeStatus {
  if (isCancelled(state, decision)) return "cancelled";
  switch (state.status) {
    case "pending":
      return "queued";
    case "awaiting_confirmation":
      return "needs approval";
    case "running":
      return "running";
    case "completed":
      return "done";
    case "error":
      return "error";
    default:
      return "queued";
  }
}

function defaultExpanded(
  part: ToolPart,
  decision?: DecisionPart | null,
): boolean {
  const state = part.state;
  if (isCancelled(state, decision)) return false;
  if (state.status === "pending") return false;
  if (state.status === "completed") return part.tool === "walkthrough";
  return true;
}

function toolMeta(part: ToolPart, conversationId: string | null): string {
  const hash = conversationId?.slice(0, 8) ?? "--------";
  const state = part.state;

  if (state.status === "awaiting_confirmation") {
    return `${hash} · ${state.estimate.label}`;
  }
  if (state.status === "running" && state.progress) {
    return `${hash} · ${state.progress.label}`;
  }
  if (state.status === "completed") {
    const stops =
      typeof state.result.stops === "number" ? `${state.result.stops} stops` : "";
    const steps =
      typeof state.result.steps === "number" ? `${state.result.steps} steps` : "";
    const detail = [stops, steps].filter(Boolean).join(" · ");
    return detail ? `${hash} · ${detail}` : hash;
  }
  if (state.status === "error") {
    return hash;
  }

  const info = getToolInfo(part.tool);
  return info ? `${hash} · ${info.short}` : hash;
}

interface ToolCardProps {
  part: ToolPart;
  decision?: DecisionPart | null;
}

export function ToolCard({ part, decision }: ToolCardProps) {
  const conversationId = useAgentRunStore((s) => s.activeConversationId);
  const [open, setOpen] = useState(() => defaultExpanded(part, decision));
  const [userToggled, setUserToggled] = useState(false);

  const state = part.state;
  const toolInfo = getToolInfo(part.tool);
  const face = getToolFace(part.tool);
  const Icon = toolInfo?.icon;
  const title = toolInfo?.name ?? part.tool;
  const status = badgeStatus(state, decision);
  const cancelled = isCancelled(state, decision);
  const awaiting = state.status === "awaiting_confirmation";
  const statusKey = `${part.tool_call_id}-${state.status}-${decision?.decision ?? ""}`;

  useEffect(() => {
    if (!userToggled) {
      setOpen(defaultExpanded(part, decision));
    }
  }, [statusKey, userToggled, part, decision]);

  const ConfigForm = face.ConfigForm;
  const DoneView = face.DoneView;

  return (
    <Collapsible
      open={open}
      onOpenChange={(next) => {
        setUserToggled(true);
        setOpen(next);
      }}
      className={cn(
        "overflow-hidden rounded-agent-card border bg-agent-bg-tool",
        awaiting ? "border-agent-warn-card-border" : "border-agent-border-subtle",
      )}
    >
      <CollapsibleTrigger asChild>
        <button
          type="button"
          aria-expanded={open}
          aria-label={`${title}, ${status}`}
          className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left transition-colors hover:bg-agent-bg-raised"
        >
          <span className="flex size-[26px] shrink-0 items-center justify-center rounded-[7px] border border-agent-accent-border bg-agent-accent-bg text-agent-accent-text">
            {Icon ? <Icon className="size-3" /> : null}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-[13px] font-semibold text-agent-text">
              {title}
            </span>
            <span className="block truncate font-agent-mono text-[10.5px] text-agent-text-faint">
              {toolMeta(part, conversationId)}
            </span>
          </span>
          <span className="ml-auto flex shrink-0 items-center gap-2">
            <ToolBadge status={status} />
            <span
              className={cn(
                "text-[10px] text-agent-text-faint transition-transform",
                open && "rotate-180",
              )}
              aria-hidden
            >
              ▾
            </span>
          </span>
        </button>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="flex flex-col gap-3.5 border-t border-agent-border px-3.5 py-3.5">
          {state.status === "pending" ? (
            <p className="animate-pulse text-xs text-agent-text-muted">
              Preparing…
            </p>
          ) : null}

          {awaiting ? (
            <ConfigForm
              part={part}
              estimate={state.estimate}
              input={state.input}
            />
          ) : null}

          {state.status === "running" && state.progress ? (
            <ToolProgress progress={state.progress} toolId={part.tool} />
          ) : null}

          {state.status === "running" && !state.progress ? (
            <p className="animate-pulse text-xs text-agent-text-muted">
              Running…
            </p>
          ) : null}

          {state.status === "completed" ? (
            <DoneView part={part} decision={decision} />
          ) : null}

          {state.status === "error" && !cancelled ? (
            <div className="rounded-agent-field border border-agent-danger-border bg-agent-danger-bg px-3 py-2.5 text-[12px] leading-relaxed text-agent-text-body">
              {state.error}
            </div>
          ) : null}

          {cancelled ? (
            <p className="text-[11px] text-agent-text-muted">
              Cancelled — you declined.
            </p>
          ) : null}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
