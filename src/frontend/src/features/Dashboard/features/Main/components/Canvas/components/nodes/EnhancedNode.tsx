import React, { memo, useMemo } from "react";
import { useParams } from "react-router-dom";
import { Handle, NodeToolbar, Position } from "@xyflow/react";
import { StepPopover } from "@/features/Dashboard/features/Agent/walkthrough/components/StepPopover";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";
import { NodeHeader } from "./NodeHeader";
import { NodeDescription } from "./NodeDescription";
import { NodeCodeView } from "./NodeCodeView";
import { NodeFooter } from "./NodeFooter";
import { useNodeCode } from "./useNodeCode";
import { NodeContextMenu } from "@/features/Dashboard/components/NodeContextMenu";
import { useNodeHandlers } from "@/features/Dashboard/hooks/useNodeHandlers";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  useAnchorSummary,
  useTaskBoard,
} from "@/features/Dashboard/features/Tasks/service/useTasks";
import { HOT_AMBER } from "@/features/Dashboard/features/Tasks/theme";
import { cn } from "@/lib/utils";

export interface NodeMetadata {
  createdAt?: string;
  updatedAt?: string;
  status?: "error" | "warning" | "success" | "idle";
  code?: string;
  language?: string;
  fileName?: string;
  description?: string;
}

export interface EnhancedNodeData {
  name: string;
  mainIcon: string | React.ReactNode;
  cornerIcon: string | React.ReactNode;
  bgColor: string;
  textColor: string;
  iconColor: string;
  borderColor: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  metadata?: NodeMetadata;
  onCodeToggle?: () => void;
  nodeId?: string;
  nodeType?: string;
  target?: { id: string };
  focused?: boolean;
  selected?: boolean;
  manuallyCreated?: boolean;
  isInjected?: boolean;
  [key: string]: unknown;
}

const EnhancedNode = memo(function EnhancedNode({
  data,
  selected,
}: {
  data: EnhancedNodeData;
  selected: boolean;
}) {
  const nodeCode = useNodeCode({
    nodeId: data.nodeId ?? "",
    targetKey: data.target?.id,
    nodeType: data.nodeType,
  });

  const activeTabId = useTabStore((s) => s.activeTabId);
  const nodeId = data.nodeId ?? "";
  const { projectId } = useParams();
  const { data: anchorSummary } = useAnchorSummary(projectId);
  const { data: taskBoard } = useTaskBoard(projectId);
  const setSelectedTaskId = useProjectStore((s) => s.setSelectedTaskId);
  const lensTaskId = useProjectStore((s) => s.lensTaskId[activeTabId]);
  const nodeTaskSummary = nodeId ? anchorSummary?.nodes[nodeId] : undefined;

  const lensMemberIds = useMemo(() => {
    if (!lensTaskId || !taskBoard) return null;
    const lensTask = taskBoard.tasks.find((t) => t.id === lensTaskId);
    if (!lensTask) return null;
    const ids = new Set<string>();
    const collect = (taskId: string) => {
      const t = taskBoard.tasks.find((x) => x.id === taskId);
      if (!t) return;
      for (const a of t.anchors) {
        if (a.is_resolved !== false) ids.add(a.node_id);
      }
      for (const s of t.subtasks) collect(s.id);
    };
    collect(lensTask.id);
    return ids;
  }, [lensTaskId, taskBoard]);
  const anchorType = useWalkthroughStore((s) => {
    const step = s.playerSteps[s.cursor];
    if (s.phase !== "playing" || !step || step.nodeId !== nodeId) return null;
    const hl = step.actions.find((a) => a.type === "highlight_lines");
    return hl ? "code-line" : "node";
  });
  const isNodePopover = anchorType === "node";
  const isCurrentStepNodeVisible = useWalkthroughStore(
    (s) => s.phase === "playing" && s.playerSteps[s.cursor]?.nodeId === nodeId,
  );

  const { statusStyles, contentStyles } = useMemo(() => {
    const status = data.metadata?.status;
    const diffStatus = data.diffStatus;

    let sStyles: React.CSSProperties = {};
    let cStyles: React.CSSProperties = {};

    // Base colors for diff statuses
    const diffBorderColors: Record<string, string> = {
      added: "#22c55e", // green-500
      modified: "#3b82f6", // blue-500
      removed: "#dc262676", // red-600 (more vibrant)
    };

    if (diffStatus && diffBorderColors[diffStatus as string]) {
      sStyles.borderColor = diffBorderColors[diffStatus as string];
      sStyles.borderWidth = "3px";

      if (diffStatus === "added" && data.isInjected) {
        sStyles.opacity = 0.6;
      }

      if (diffStatus === "removed") {
        sStyles.opacity = 0.6;
        cStyles.filter = "grayscale(100%) brightness(2)"; // Brighten to make white text pop on red
        sStyles.backgroundColor = "#dc2626"; // red-600
        sStyles.color = "#ffffff";
        sStyles.pointerEvents = "none";
      }
    }

    if (status && status !== "idle") {
      const colors: Record<string, string> = {
        error: "#ef4444",
        warning: "#f59e0b",
        success: "#10b981",
      };
      if (!sStyles.borderColor) {
        sStyles.borderColor = colors[status];
      }
      sStyles.boxShadow = `0 0 10px ${colors[status]}55`;
    }

    if (nodeTaskSummary?.hot) {
      sStyles.borderColor = HOT_AMBER;
      sStyles.boxShadow = `0 0 12px ${HOT_AMBER}66`;
    }

    if (lensMemberIds) {
      if (!lensMemberIds.has(nodeId)) {
        sStyles.opacity = 0.15;
      } else {
        sStyles.boxShadow = `0 0 0 2px #4ade8066`;
      }
    }

    return { statusStyles: sStyles, contentStyles: cStyles };
  }, [
    data.metadata?.status,
    data.diffStatus,
    nodeTaskSummary?.hot,
    lensMemberIds,
    nodeId,
  ]);

  const { onAction } = useNodeHandlers(data.nodeId ?? "", activeTabId);

  const handleCodeToggle = () => {
    nodeCode.toggleCode();
    data.onCodeToggle?.();
  };

  const hasStatusOverride = Object.keys(statusStyles).length > 0;
  const descriptionFallback =
    data.nodeType && data.name
      ? `${data.nodeType.charAt(0).toUpperCase()}${data.nodeType.slice(1)} ${data.name}`
      : undefined;
  const customIconColor =
    data.iconColor && data.iconColor !== "var(--primary)"
      ? data.iconColor
      : undefined;

  return (
    <>
      <NodeToolbar
        isVisible={isNodePopover}
        position={Position.Left}
        align="center"
        offset={16}
      >
        <StepPopover />
      </NodeToolbar>

      <div
        data-node-id={nodeId}
        data-walkthrough-node-anchor={isCurrentStepNodeVisible ? "" : undefined}
        className={cn(
          "canvas-node walkthrough-node relative min-w-[300px] max-w-[320px] overflow-hidden rounded-(--radius) border border-border bg-card text-card-foreground transition-shadow",
          selected &&
            "ring-2 ring-chart-4 ring-offset-2 ring-offset-background",
          isCurrentStepNodeVisible && "walkthrough-active-node",
        )}
        style={hasStatusOverride ? statusStyles : undefined}
      >
        <NodeContextMenu
          nodeId={data.nodeId ?? ""}
          nodeType={data.nodeType ?? ""}
          manuallyCreated={data.manuallyCreated}
          onAction={onAction}
        >
          <div style={contentStyles}>
            <NodeHeader
              name={data.name}
              icon={data.mainIcon}
              iconColor={customIconColor}
              expandable={data.expandable}
              expanded={data.expanded}
              onToggle={data.onToggle}
              hasCode={Boolean(nodeCode.hasCode)}
              showCode={nodeCode.showCode}
              onCodeToggle={handleCodeToggle}
              status={data.metadata?.status}
              diffStatus={data.diffStatus as any}
              taskOpenCount={nodeTaskSummary?.open_count}
              taskHot={nodeTaskSummary?.hot}
              onTaskBadgeClick={() => {
                const firstTaskId = nodeTaskSummary?.open_task_ids[0];
                if (firstTaskId) setSelectedTaskId(firstTaskId);
              }}
            />

            {nodeCode.showCode && nodeCode.hasCode ? (
              <NodeCodeView
                code={nodeCode.code}
                fileName={nodeCode.fileName}
                language={nodeCode.language}
                onChange={nodeCode.setCode}
                onSave={nodeCode.handleSave}
                hasChanges={nodeCode.hasChanges}
                isSaving={nodeCode.isSaving}
                isLoading={nodeCode.isLoading}
                showDiff={nodeCode.showDiff}
                originalContent={nodeCode.originalContent}
                modifiedContent={nodeCode.modifiedContent}
                isLoadingDiff={nodeCode.isLoadingDiff}
                diffError={nodeCode.diffError}
                borderColor={
                  (statusStyles.borderColor as string) || data.borderColor
                }
                iconColor={(statusStyles.color as string) || data.iconColor}
                nodeId={data.nodeId ?? ""}
                nodeStartLine={nodeCode.nodeStartLine}
                isWalkthroughPlaying={nodeCode.isWalkthroughPlaying}
              />
            ) : (
              <NodeDescription
                description={data.metadata?.description}
                fallbackLabel={descriptionFallback}
              />
            )}

            <NodeFooter
              createdAt={data.metadata?.createdAt}
              updatedAt={data.metadata?.updatedAt}
            />
          </div>
        </NodeContextMenu>

        <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
        <Handle
          type="source"
          position={Position.Right}
          style={{ opacity: 0 }}
        />
      </div>
    </>
  );
});

export default EnhancedNode;
