import { useEffect, useMemo, useState } from "react";
import { Play } from "lucide-react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useDecision } from "../../../hooks/useDecision";
import type { ToolEstimate, ToolPart } from "../../../stream/types";
import { getToolInfo } from "../../../tools/registry";
import { DepthSlider } from "../../controls/DepthSlider";
import { Segmented, type DetailLevel } from "../../controls/Segmented";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

interface WalkthroughConfigFormProps {
  part: ToolPart;
  estimate: ToolEstimate;
  input: Record<string, unknown>;
}

export function WalkthroughConfigForm({
  part,
  estimate,
  input,
}: WalkthroughConfigFormProps) {
  const { decide } = useDecision();
  const projectId = useProjectStore((s) => s.projectData?.id);
  const [submitting, setSubmitting] = useState(false);
  const runLabel = getToolInfo(part.tool)?.runLabel ?? "Run";

  const knobs = estimate.knobs ?? {};
  const depthKnob = (knobs.depth ?? {}) as {
    min?: number;
    max?: number;
    suggested?: number;
  };
  const minDepth = typeof depthKnob.min === "number" ? depthKnob.min : 1;
  const maxDepth = typeof depthKnob.max === "number" ? depthKnob.max : 5;
  const treeMax = maxDepth;
  const suggested =
    typeof depthKnob.suggested === "number"
      ? depthKnob.suggested
      : typeof input.depth === "number"
        ? (input.depth as number)
        : minDepth;

  const [depth, setDepth] = useState(
    Math.min(maxDepth, Math.max(minDepth, suggested)),
  );
  const [verbosity, setVerbosity] = useState<DetailLevel>(
    ((input.verbosity as DetailLevel) || "normal") as DetailLevel,
  );
  const [liveLabel, setLiveLabel] = useState(estimate.label);

  const originalDepth =
    typeof input.depth === "number" ? (input.depth as number) : suggested;
  const originalVerbosity = (input.verbosity as DetailLevel) || "normal";

  useEffect(() => {
    if (!projectId || typeof input.node_id !== "string") return;
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({
        node_id: input.node_id as string,
        depth: String(depth),
        project_id: projectId,
      });
      void fetch(`${API_BASE}/walkthroughs/estimate?${params}`)
        .then(async (res) => {
          if (!res.ok) return;
          const data = (await res.json()) as {
            node_count?: number;
            llm_call_estimate?: number;
          };
          if (data.node_count != null && data.llm_call_estimate != null) {
            setLiveLabel(
              `${data.node_count} stops · ~${data.llm_call_estimate} LLM calls`,
            );
          }
        })
        .catch(() => undefined);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [depth, input.node_id, projectId]);

  const overrides = useMemo(() => {
    const next: Record<string, unknown> = {};
    if (depth !== originalDepth) next.depth = depth;
    if (verbosity !== originalVerbosity) next.verbosity = verbosity;
    return next;
  }, [depth, originalDepth, originalVerbosity, verbosity]);

  const submit = async (decision: "approve" | "cancel") => {
    setSubmitting(true);
    try {
      await decide(
        part.tool_call_id,
        decision,
        decision === "approve" ? overrides : undefined,
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (estimate.over_cap) {
    return (
      <div className="space-y-2 text-xs text-agent-text-muted">
        <p>{estimate.label} exceeds the visit cap.</p>
        <p>Lower the depth and ask again.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3.5">
      <DepthSlider
        value={depth}
        onChange={setDepth}
        min={minDepth}
        max={maxDepth}
        treeMax={treeMax}
      />
      <Segmented value={verbosity} onChange={setVerbosity} />
      <p className="text-[11px] text-agent-text-faint">
        {liveLabel} is above the auto-run limit — that&apos;s why we&apos;re
        asking.
      </p>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          disabled={submitting}
          onClick={() => void submit("cancel")}
          className="rounded-agent-field px-3 py-2 text-xs text-agent-text-muted transition-colors hover:bg-agent-bg-raised hover:text-agent-text disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={() => void submit("approve")}
          className="inline-flex items-center gap-1.5 rounded-agent-field border border-agent-btn-border bg-agent-btn px-3 py-2 text-xs font-semibold text-agent-on-btn transition-colors hover:bg-agent-btn-hover disabled:opacity-50"
        >
          <Play className="size-3 fill-current" />
          {runLabel}
        </button>
      </div>
    </div>
  );
}
