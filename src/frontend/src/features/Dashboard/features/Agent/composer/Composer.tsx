import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useShallow } from "zustand/react/shallow";
import { useRunStream } from "../hooks/useRunStream";
import {
  MAX_ATTACHMENTS,
  useAgentRunStore,
} from "../store/useAgentRunStore";
import type { NodeRefPart, Part } from "../stream/types";
import {
  getToolInfo,
  isAvailable,
  type ToolId,
} from "../tools/registry";
import { EffortPicker } from "./EffortPicker";
import { NodeChip } from "./NodeChip";
import { ToolPicker } from "./ToolPicker";

const MAX_TEXTAREA_ROWS = 8;
const LINE_HEIGHT_PX = 20;

function selectedToNodeRef(node: {
  id: string;
  name: string;
  node_type: string;
  qname?: string | null;
}): NodeRefPart {
  return {
    type: "node_ref",
    node_id: node.id,
    name: node.name,
    qname: node.qname ?? null,
    node_type: node.node_type,
  };
}

interface ComposerProps {
  onFocusNode?: (part: NodeRefPart) => void;
}

export function Composer({ onFocusNode }: ComposerProps) {
  const [value, setValue] = useState("");
  const [toolMenuOpen, setToolMenuOpen] = useState(false);
  const [effortMenuOpen, setEffortMenuOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { send, stop, isStreaming, conversation } = useRunStream();
  const [
    effort,
    setEffort,
    selectedToolId,
    setSelectedToolId,
    pendingAttachments,
    addAttachment,
    removeAttachment,
    clearAttachments,
  ] = useAgentRunStore(
    useShallow((s) => [
      s.effort,
      s.setEffort,
      s.selectedToolId,
      s.setSelectedToolId,
      s.pendingAttachments,
      s.addAttachment,
      s.removeAttachment,
      s.clearAttachments,
    ]),
  );

  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);
  const selectedTool = getToolInfo(selectedToolId);

  const runStatus = conversation?.status ?? "idle";
  const awaitingDecision = runStatus === "awaiting_confirmation";
  const hasDraft = value.trim().length > 0;
  const hasAttachments = pendingAttachments.length > 0;
  const canSendDefault =
    isAvailable(selectedToolId) && hasAttachments && !hasDraft;
  const canSend =
    !isStreaming &&
    !awaitingDecision &&
    (hasDraft || hasAttachments);

  const attachDisabled = useMemo(() => {
    if (!selectedNode) return true;
    if (pendingAttachments.length >= MAX_ATTACHMENTS) return true;
    return pendingAttachments.some((p) => p.node_id === selectedNode.id);
  }, [pendingAttachments, selectedNode]);

  const resizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = LINE_HEIGHT_PX * MAX_TEXTAREA_ROWS;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, []);

  useEffect(() => {
    resizeTextarea();
  }, [value, resizeTextarea]);

  const handleAttach = () => {
    if (!selectedNode || attachDisabled) return;
    addAttachment(selectedToNodeRef(selectedNode));
  };

  const handleSend = () => {
    if (!canSend || isStreaming || awaitingDecision) return;

    const tool = getToolInfo(selectedToolId);
    const text = value.trim() || (canSendDefault ? tool?.defaultPrompt ?? "" : "");
    if (!text && pendingAttachments.length === 0) return;

    const parts: Part[] = [
      ...pendingAttachments,
      ...(text ? [{ type: "text" as const, text }] : []),
    ];
    setValue("");
    clearAttachments();
    void send(parts, {
      toolHint: isAvailable(selectedToolId) ? selectedToolId : undefined,
    });
  };

  const closeMenus = () => {
    setToolMenuOpen(false);
    setEffortMenuOpen(false);
  };

  const sendDisabledReason = awaitingDecision
    ? "Waiting for your decision above"
    : !hasDraft && !hasAttachments
      ? "Attach a node or type a message"
      : null;

  const placeholder = awaitingDecision
    ? "Waiting for your decision above…"
    : selectedTool
      ? `Ask the agent, or run ${selectedTool.name.toLowerCase()}…`
      : "Ask the agent…";

  return (
    <div className="shrink-0 border-t border-agent-header-border px-3.5 pt-3 pb-3.5">
      <div className="rounded-agent-card border border-agent-border-strong bg-agent-bg-card px-3 pt-2.5 pb-2 focus-within:border-agent-border-strong/80">
        <textarea
          ref={textareaRef}
          rows={2}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              if (toolMenuOpen || effortMenuOpen) {
                event.preventDefault();
                closeMenus();
                return;
              }
              event.currentTarget.blur();
              return;
            }
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          disabled={awaitingDecision}
          placeholder={placeholder}
          aria-label="Message composer"
          className="max-h-[160px] w-full resize-none border-none bg-transparent text-[13.5px] leading-5 text-agent-text placeholder:text-agent-text-faint focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
        />
        <div className="flex flex-wrap items-center gap-1.5 pt-1.5">
          {pendingAttachments.map((part) => (
            <NodeChip
              key={part.node_id}
              part={part}
              onFocus={onFocusNode}
              onRemove={() => removeAttachment(part.node_id)}
            />
          ))}
          {!pendingAttachments.length && selectedNode ? (
            <button
              type="button"
              disabled={attachDisabled || awaitingDecision}
              onClick={handleAttach}
              className="inline-flex items-center gap-1.5 rounded-agent-field border border-agent-border-strong bg-agent-bg-raised px-2.5 py-1.5 font-agent-mono text-[12px] text-agent-text-muted transition-colors hover:text-agent-text disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span
                className="size-1.5 rounded-sm bg-agent-text-muted"
                aria-hidden
              />
              {selectedNode.name}
              <span className="text-agent-text-faint">{selectedNode.node_type}</span>
            </button>
          ) : null}
          <ToolPicker
            selectedId={selectedToolId}
            onSelect={(id: ToolId) => setSelectedToolId(id)}
            open={toolMenuOpen}
            onOpenChange={setToolMenuOpen}
            disabled={awaitingDecision}
          />
          <div className="ml-auto flex items-center gap-1.5">
            <EffortPicker
              value={effort}
              onChange={setEffort}
              open={effortMenuOpen}
              onOpenChange={setEffortMenuOpen}
              disabled={awaitingDecision}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={() => void stop()}
                aria-label="Stop"
                className="flex size-8 items-center justify-center rounded-[9px] border border-agent-danger-border bg-agent-danger-bg text-agent-danger transition-colors hover:bg-agent-danger-bg/80"
              >
                <Square className="size-3" />
              </button>
            ) : (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={!canSend}
                    aria-label="Send message"
                    className="flex size-8 items-center justify-center rounded-[9px] border border-agent-btn-border bg-agent-btn text-agent-on-btn transition-colors hover:bg-agent-btn-hover disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <ArrowUp className="size-3.5" strokeWidth={2} />
                  </button>
                </TooltipTrigger>
                {sendDisabledReason ? (
                  <TooltipContent side="top" className="text-xs">
                    {sendDisabledReason}
                  </TooltipContent>
                ) : null}
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
