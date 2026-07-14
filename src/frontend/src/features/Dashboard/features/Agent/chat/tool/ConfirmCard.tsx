import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/ui/toggle-group";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useDecision } from "../../hooks/useDecision";
import type { ToolEstimate, ToolPart } from "../../stream/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

type Verbosity = "quick" | "normal" | "detailed";

interface ConfirmCardProps {
  part: ToolPart;
  estimate: ToolEstimate;
  input: Record<string, unknown>;
}

export function ConfirmCard({ part, estimate, input }: ConfirmCardProps) {
  const { decide } = useDecision();
  const projectId = useProjectStore((s) => s.projectData?.id);
  const [submitting, setSubmitting] = useState(false);

  const knobs = estimate.knobs ?? {};
  const depthKnob = (knobs.depth ?? {}) as {
    min?: number;
    max?: number;
    suggested?: number;
  };
  const minDepth = typeof depthKnob.min === "number" ? depthKnob.min : 0;
  const maxDepth = typeof depthKnob.max === "number" ? depthKnob.max : 5;
  const suggested =
    typeof depthKnob.suggested === "number"
      ? depthKnob.suggested
      : typeof input.depth === "number"
        ? (input.depth as number)
        : minDepth;

  const [depth, setDepth] = useState(
    Math.min(maxDepth, Math.max(minDepth, suggested)),
  );
  const [verbosity, setVerbosity] = useState<Verbosity>(
    (input.verbosity as Verbosity) || "normal",
  );
  const [liveLabel, setLiveLabel] = useState(estimate.label);

  const originalDepth =
    typeof input.depth === "number" ? (input.depth as number) : suggested;
  const originalVerbosity = (input.verbosity as Verbosity) || "normal";

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
            over_cap?: boolean;
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
      <div className="space-y-2 text-xs text-muted-foreground">
        <p>{estimate.label} exceeds the visit cap.</p>
        <p>Lower the depth and ask again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 text-xs">
      <p className="text-foreground">
        {typeof input.node_id === "string" ? (
          <span className="font-medium">
            {(input as { name?: string }).name ??
              String(input.node_id).split("/").pop()}
          </span>
        ) : null}
        <span className="text-muted-foreground"> · {liveLabel}</span>
      </p>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label className="text-[11px]">Depth</Label>
          <span className="text-[11px] text-muted-foreground">
            {depth} (this tree: max {maxDepth})
          </span>
        </div>
        <Slider
          min={minDepth}
          max={Math.max(minDepth, maxDepth)}
          step={1}
          value={[depth]}
          onValueChange={(v) => setDepth(v[0] ?? minDepth)}
        />
      </div>

      <div className="space-y-1.5">
        <Label className="text-[11px]">Detail</Label>
        <ToggleGroup
          type="single"
          size="sm"
          value={verbosity}
          onValueChange={(v) => {
            if (v) setVerbosity(v as Verbosity);
          }}
          className="justify-start"
        >
          <ToggleGroupItem value="quick" className="text-[11px]">
            Quick
          </ToggleGroupItem>
          <ToggleGroupItem value="normal" className="text-[11px]">
            Normal
          </ToggleGroupItem>
          <ToggleGroupItem value="detailed" className="text-[11px]">
            Detailed
          </ToggleGroupItem>
        </ToggleGroup>
      </div>

      <p className="text-[11px] text-muted-foreground">
        Bigger than the auto-run limit — that&apos;s why we&apos;re asking.
      </p>

      <div className="flex justify-end gap-2">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          className="h-8 text-[11px]"
          disabled={submitting}
          onClick={() => void submit("cancel")}
        >
          Cancel
        </Button>
        <Button
          type="button"
          size="sm"
          className="h-8 text-[11px]"
          disabled={submitting}
          onClick={() => void submit("approve")}
        >
          ▶ Run tour
        </Button>
      </div>
    </div>
  );
}
