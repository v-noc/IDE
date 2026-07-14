import { useMemo, useState } from "react";
import { Play, SendHorizontal, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useShallow } from "zustand/react/shallow";
import { useRunStream } from "../hooks/useRunStream";
import {
  MAX_ATTACHMENTS,
  useAgentRunStore,
} from "../store/useAgentRunStore";
import type { EffortLevel, NodeRefPart, Part } from "../stream/types";
import { NodeRefChipView } from "./parts/NodeRefChip";

const EFFORT_OPTIONS: EffortLevel[] = ["off", "low", "medium", "high"];

function selectedToNodeRef(
  node: {
    id: string;
    name: string;
    node_type: string;
    qname?: string | null;
  },
): NodeRefPart {
  return {
    type: "node_ref",
    node_id: node.id,
    name: node.name,
    qname: node.qname ?? null,
    node_type: node.node_type,
  };
}

interface ComposerProps {
  className?: string;
  onFocusNode?: (part: NodeRefPart) => void;
}

export function Composer({ className, onFocusNode }: ComposerProps) {
  const [value, setValue] = useState("");
  const { send, stop, isStreaming, conversation } = useRunStream();
  const [
    effort,
    setEffort,
    pendingAttachments,
    addAttachment,
    removeAttachment,
    clearAttachments,
  ] = useAgentRunStore(
    useShallow((s) => [
      s.effort,
      s.setEffort,
      s.pendingAttachments,
      s.addAttachment,
      s.removeAttachment,
      s.clearAttachments,
    ]),
  );

  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);

  const runStatus = conversation?.status ?? "idle";
  const awaitingDecision = runStatus === "awaiting_confirmation";
  const canSend =
    !isStreaming &&
    !awaitingDecision &&
    (value.trim().length > 0 || pendingAttachments.length > 0);

  const attachDisabled = useMemo(() => {
    if (!selectedNode) return true;
    if (pendingAttachments.length >= MAX_ATTACHMENTS) return true;
    return pendingAttachments.some((p) => p.node_id === selectedNode.id);
  }, [pendingAttachments, selectedNode]);

  const handleAttach = () => {
    if (!selectedNode || attachDisabled) return;
    addAttachment(selectedToNodeRef(selectedNode));
  };

  const handleSend = (textOverride?: string) => {
    const text = (textOverride ?? value).trim();
    if (!text && pendingAttachments.length === 0) return;
    if (isStreaming || awaitingDecision) return;

    const parts: Part[] = [
      ...pendingAttachments,
      ...(text ? [{ type: "text" as const, text }] : []),
    ];
    setValue("");
    clearAttachments();
    void send(parts);
  };

  const handleWalkthrough = () => {
    if (!pendingAttachments.length && !selectedNode) return;
    if (!pendingAttachments.length && selectedNode) {
      addAttachment(selectedToNodeRef(selectedNode));
    }
    // Defer send so the attachment just added is included
    queueMicrotask(() => {
      const attachments = useAgentRunStore.getState().pendingAttachments;
      if (!attachments.length) return;
      const parts: Part[] = [
        ...attachments,
        {
          type: "text",
          text: "Generate a walkthrough of this node.",
        },
      ];
      clearAttachments();
      setValue("");
      void send(parts);
    });
  };

  return (
    <div className={cn("space-y-2", className)}>
      {pendingAttachments.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {pendingAttachments.map((part) => (
            <NodeRefChipView
              key={part.node_id}
              part={part}
              onFocus={onFocusNode}
              onRemove={() => removeAttachment(part.node_id)}
            />
          ))}
        </div>
      ) : null}

      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSend();
          }
        }}
        placeholder={
          awaitingDecision
            ? "Waiting for your decision above…"
            : "Ask AI about this code…"
        }
        rows={2}
        disabled={awaitingDecision}
        className="min-h-[2.5rem] w-full resize-none rounded-md border border-input bg-transparent px-3 py-2 text-xs shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
      />

      <div className="flex flex-wrap items-center gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-8 px-2 text-[11px]"
                disabled={attachDisabled || awaitingDecision}
                onClick={handleAttach}
              >
                ⬡ Attach selected
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">
              {pendingAttachments.length >= MAX_ATTACHMENTS
                ? `Max ${MAX_ATTACHMENTS} attachments (enrichment cap)`
                : selectedNode
                  ? `Attach ${selectedNode.name}`
                  : "Select a node on the canvas first"}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-8 px-2 text-[11px]"
          disabled={
            awaitingDecision ||
            isStreaming ||
            (!pendingAttachments.length && !selectedNode)
          }
          onClick={handleWalkthrough}
        >
          <Play size={12} className="mr-1" />
          Walkthrough
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-8 px-2 text-[11px] text-muted-foreground"
              disabled={awaitingDecision}
            >
              ✧ {effort}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuRadioGroup
              value={effort}
              onValueChange={(v) => setEffort(v as EffortLevel)}
            >
              {EFFORT_OPTIONS.map((option) => (
                <DropdownMenuRadioItem
                  key={option}
                  value={option}
                  className="text-xs"
                >
                  {option}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="ml-auto">
          {isStreaming ? (
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => void stop()}
              className="h-8 px-3"
              aria-label="Stop"
            >
              <Square size={12} />
            </Button>
          ) : (
            <Button
              type="button"
              size="sm"
              onClick={() => handleSend()}
              disabled={!canSend}
              className="h-8 px-3"
              aria-label="Send message"
            >
              <SendHorizontal size={14} />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
