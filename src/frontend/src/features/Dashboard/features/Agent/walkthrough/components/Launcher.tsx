import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useShallow } from "zustand/react/shallow";
import { walkthroughSource } from "../source";
import type { Estimate } from "../types";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

const DEPTH_OPTIONS = [
  { value: "0", label: "This node only" },
  { value: "1", label: "Depth 1" },
  { value: "2", label: "Depth 2" },
  { value: "3", label: "Depth 3" },
] as const;

export function Launcher() {
  const activeTabId = useTabStore((s) => s.activeTabId);
  const [selectedNode, projectId] = useProjectStore(
    useShallow((s) => [s.selectedNode[activeTabId], s.projectData?.id]),
  );
  const [phase, start, discard] = useWalkthroughStore(
    useShallow((s) => [s.phase, s.start, s.discard]),
  );

  const [depth, setDepth] = useState("1");
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [estimating, setEstimating] = useState(false);
  const [estimateError, setEstimateError] = useState<string | null>(null);

  const nodeLabel = selectedNode
    ? `${selectedNode.name} (${selectedNode.node_type})`
    : "No node selected";

  const loadEstimate = useCallback(async () => {
    if (!selectedNode || !projectId) return;

    setEstimating(true);
    setEstimateError(null);

    try {
      const result = await walkthroughSource.estimate({
        project_id: projectId,
        node_id: selectedNode.id,
        depth: Number(depth),
      });
      setEstimate(result);
    } catch (err) {
      setEstimate(null);
      setEstimateError(
        err instanceof Error ? err.message : "Could not load estimate",
      );
    } finally {
      setEstimating(false);
    }
  }, [depth, projectId, selectedNode]);

  const handleGenerate = () => {
    if (!selectedNode || !projectId) return;

    if (phase !== "idle" && phase !== "ready" && phase !== "error") {
      const confirmed = window.confirm(
        "Discard the current walkthrough and generate a new one?",
      );
      if (!confirmed) return;
      discard();
    }

    start(
      {
        project_id: projectId,
        node_id: selectedNode.id,
        depth: Number(depth),
      },
      activeTabId,
    );
  };

  const isGenerating = phase === "generating";
  const canGenerate = Boolean(selectedNode && projectId);

  return (
    <section className="space-y-3 rounded-md border border-border bg-muted/30 p-3">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          Launcher
        </p>
        <p className="mt-1 text-xs text-foreground">
          Use selected: <span className="font-medium">{nodeLabel}</span>
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="walkthrough-depth" className="text-xs">
          Depth
        </Label>
        <select
          id="walkthrough-depth"
          value={depth}
          onChange={(event) => setDepth(event.target.value)}
          className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs"
        >
          {DEPTH_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!selectedNode || !projectId || estimating}
          onClick={() => void loadEstimate()}
        >
          {estimating ? "Estimating…" : "Estimate"}
        </Button>
        {estimate ? (
          <p className="text-[11px] text-muted-foreground">
            {estimate.node_count} stops · ~{estimate.step_estimate} steps · ~
            {estimate.llm_call_estimate} calls
            {estimate.over_cap ? " · over cap" : ""}
          </p>
        ) : null}
      </div>

      {estimateError ? (
        <p className="text-[11px] text-destructive">{estimateError}</p>
      ) : null}

      <Button
        type="button"
        size="sm"
        className="w-full"
        disabled={!canGenerate || isGenerating || estimate?.over_cap}
        onClick={handleGenerate}
      >
        {isGenerating ? "Generating…" : "Generate walkthrough"}
      </Button>
    </section>
  );
}
