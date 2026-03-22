import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { useAgentUiStore } from "@/features/Dashboard/features/Agent/store/useAgentUiStore";
import { useAgentOverlayStore } from "@/features/Dashboard/features/Agent/store/useAgentOverlayStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import queryKeys from "@/lib/queryKeys";
import { AgentHttpError } from "@/lib/agentFetch";
import {
  agentConversationHydrationQueryOptions,
  agentWorkflowsApi,
} from "@/services/agent";
import type { AnyNodeTree } from "@/types/project";
import type {
  DescriptionWorkflowMode,
  DocumentationWorkflowMode,
  RunWorkflowBatchRequest,
  WorkflowBatchStepWire,
  WorkflowModelId,
} from "@/types/agent/workflows";
import { WORKFLOW_MODEL_OPTIONS } from "@/types/agent/workflows";

type Scope = "description" | "documentation" | "both";

function buildWorkflowSteps(args: {
  scope: Scope;
  nodeId: string;
  descriptionModel: WorkflowModelId;
  documentationModel: WorkflowModelId;
  descriptionMode: DescriptionWorkflowMode;
  documentationMode: DocumentationWorkflowMode;
  direction: "up" | "down";
  maxDepth: number;
}): WorkflowBatchStepWire[] {
  const base = {
    node_id: args.nodeId,
    direction: args.direction,
    max_depth: args.maxDepth,
  };
  const steps: WorkflowBatchStepWire[] = [];
  if (args.scope === "description" || args.scope === "both") {
    steps.push({
      workflow_name: "description_generator",
      params: {
        ...base,
        model: args.descriptionModel,
        description_mode: args.descriptionMode,
      },
    });
  }
  if (args.scope === "documentation" || args.scope === "both") {
    steps.push({
      workflow_name: "documentation_generator",
      params: {
        ...base,
        model: args.documentationModel,
        documentation_mode: args.documentationMode,
      },
    });
  }
  return steps;
}

interface StartWorkflowDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targetNode: AnyNodeTree;
  projectId: string;
}

export function StartWorkflowDialog({
  open,
  onOpenChange,
  targetNode,
  projectId,
}: StartWorkflowDialogProps) {
  const queryClient = useQueryClient();
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);
  const setAgentOpen = useAgentOverlayStore((s) => s.setOpen);
  const setBackendConversationId = useAgentUiStore(
    (s) => s.setBackendConversationId,
  );

  const [scope, setScope] = useState<Scope>("both");
  const [conversationTitle, setConversationTitle] = useState("");
  const [conversationDescription, setConversationDescription] = useState("");
  const [descriptionModel, setDescriptionModel] =
    useState<WorkflowModelId>("gpt-4o-mini");
  const [documentationModel, setDocumentationModel] =
    useState<WorkflowModelId>("gpt-4o-mini");
  const [descriptionMode, setDescriptionMode] =
    useState<DescriptionWorkflowMode>("always");
  const [documentationMode, setDocumentationMode] =
    useState<DocumentationWorkflowMode>("upsert");
  const [direction, setDirection] = useState<"up" | "down">("down");
  const [maxDepth, setMaxDepth] = useState(5);

  const nodeId = targetNode.id;

  const resetForm = () => {
    setScope("both");
    setConversationTitle("");
    setConversationDescription("");
    setDescriptionModel("gpt-4o-mini");
    setDocumentationModel("gpt-4o-mini");
    setDescriptionMode("always");
    setDocumentationMode("upsert");
    setDirection("down");
    setMaxDepth(5);
  };

  const batchMutation = useMutation({
    mutationFn: (body: RunWorkflowBatchRequest) =>
      agentWorkflowsApi.runBatch(projectId, body),
    onSuccess: async (data) => {
      toast.success("Workflows started");
      const cid = data.conversation_id;
      setBackendConversationId(cid);
      setAgentOpen(true);
      await queryClient.prefetchQuery(
        agentConversationHydrationQueryOptions(
          projectId,
          cid,
          branch,
          ref,
          compareTo,
          200,
        ),
      );
      void queryClient.invalidateQueries({
        queryKey: queryKeys.agent.conversations.all(),
      });
      onOpenChange(false);
      resetForm();
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof AgentHttpError
          ? JSON.stringify(err.body) || err.message
          : err instanceof Error
            ? err.message
            : "Failed to start workflows";
      toast.error(msg);
    },
  });

  const payload = useMemo((): RunWorkflowBatchRequest | null => {
    if (!nodeId) return null;
    const steps = buildWorkflowSteps({
      scope,
      nodeId,
      descriptionModel,
      documentationModel,
      descriptionMode,
      documentationMode,
      direction,
      maxDepth,
    });
    const body: RunWorkflowBatchRequest = { steps };
    const t = conversationTitle.trim();
    const d = conversationDescription.trim();
    if (t) body.conversation_title = t;
    if (d) body.conversation_description = d;
    return body;
  }, [
    nodeId,
    scope,
    descriptionModel,
    documentationModel,
    descriptionMode,
    documentationMode,
    direction,
    maxDepth,
    conversationTitle,
    conversationDescription,
  ]);

  const handleSubmit = () => {
    if (!payload?.steps.length) {
      toast.error("Select at least one workflow step");
      return;
    }
    batchMutation.mutate(payload);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) resetForm();
      }}
    >
      <DialogContent className="max-h-[min(90vh,720px)] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Start workflow</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Root: <span className="font-medium text-foreground">{targetNode.name}</span>
          </p>
        </DialogHeader>

        <div className="space-y-6 py-2">
          <div className="space-y-2">
            <Label>Run</Label>
            <RadioGroup
              value={scope}
              onValueChange={(v) => setScope(v as Scope)}
              className="flex flex-col gap-2"
            >
              <label className="flex items-center gap-2 text-sm">
                <RadioGroupItem value="description" id="wf-scope-desc" />
                <span>Update descriptions only</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <RadioGroupItem value="documentation" id="wf-scope-doc" />
                <span>Documentation only</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <RadioGroupItem value="both" id="wf-scope-both" />
                <span>Descriptions then documentation</span>
              </label>
            </RadioGroup>
          </div>

          {(scope === "description" || scope === "both") && (
            <div className="space-y-3 rounded-md border border-border/60 p-3">
              <p className="text-sm font-medium">Descriptions</p>
              <div className="space-y-2">
                <Label htmlFor="wf-desc-model">Model</Label>
                <select
                  id="wf-desc-model"
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  value={descriptionModel}
                  onChange={(e) =>
                    setDescriptionModel(e.target.value as WorkflowModelId)
                  }
                >
                  {WORKFLOW_MODEL_OPTIONS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Existing descriptions</Label>
                <RadioGroup
                  value={descriptionMode}
                  onValueChange={(v) =>
                    setDescriptionMode(v as DescriptionWorkflowMode)
                  }
                  className="flex flex-col gap-2"
                >
                  <label className="flex items-center gap-2 text-sm">
                    <RadioGroupItem value="always" id="wf-desc-always" />
                    <span>Regenerate all</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <RadioGroupItem
                      value="skip_if_present"
                      id="wf-desc-skip"
                    />
                    <span>Skip nodes that already have a description</span>
                  </label>
                </RadioGroup>
              </div>
            </div>
          )}

          {(scope === "documentation" || scope === "both") && (
            <div className="space-y-3 rounded-md border border-border/60 p-3">
              <p className="text-sm font-medium">Documentation</p>
              <div className="space-y-2">
                <Label htmlFor="wf-doc-model">Model</Label>
                <select
                  id="wf-doc-model"
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  value={documentationModel}
                  onChange={(e) =>
                    setDocumentationModel(e.target.value as WorkflowModelId)
                  }
                >
                  {WORKFLOW_MODEL_OPTIONS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Write mode</Label>
                <RadioGroup
                  value={documentationMode}
                  onValueChange={(v) =>
                    setDocumentationMode(v as DocumentationWorkflowMode)
                  }
                  className="flex flex-col gap-2"
                >
                  <label className="flex items-center gap-2 text-sm">
                    <RadioGroupItem value="upsert" id="wf-doc-upsert" />
                    <span>Upsert (replace generated doc content)</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <RadioGroupItem value="insert_only" id="wf-doc-insert" />
                    <span>Insert only if no generated doc exists yet</span>
                  </label>
                </RadioGroup>
              </div>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="wf-direction">Traversal</Label>
              <select
                id="wf-direction"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                value={direction}
                onChange={(e) =>
                  setDirection(e.target.value as "up" | "down")
                }
              >
                <option value="down">Top-down</option>
                <option value="up">Bottom-up</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="wf-depth">Max depth</Label>
              <Input
                id="wf-depth"
                type="number"
                min={1}
                max={32}
                value={maxDepth}
                onChange={(e) =>
                  setMaxDepth(Math.max(1, Number(e.target.value) || 1))
                }
              />
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium">Conversation (optional)</p>
            <div className="space-y-2">
              <Label htmlFor="wf-conv-title">Title</Label>
              <Input
                id="wf-conv-title"
                placeholder="Defaults to an auto title if empty"
                value={conversationTitle}
                onChange={(e) => setConversationTitle(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="wf-conv-desc">Description</Label>
              <Textarea
                id="wf-conv-desc"
                placeholder="Defaults to an auto summary if empty"
                rows={2}
                value={conversationDescription}
                onChange={(e) => setConversationDescription(e.target.value)}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={batchMutation.isPending || !nodeId}
          >
            {batchMutation.isPending ? "Starting…" : "Start"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
