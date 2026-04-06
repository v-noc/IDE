import React, { memo, useMemo } from "react";
import { Handle, Position } from "@xyflow/react";
import { NodeHeader } from "./NodeHeader";
import { NodeDescription } from "./NodeDescription";
import { NodeCodeView } from "./NodeCodeView";
import { NodeFooter } from "./NodeFooter";
import { useNodeCode } from "./useNodeCode";
import { NodeContextMenu } from "@/features/Dashboard/components/NodeContextMenu";
import { useNodeHandlers } from "@/features/Dashboard/hooks/useNodeHandlers";
import useTabStore from "@/features/Dashboard/store/useTabStore";

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

    return { statusStyles: sStyles, contentStyles: cStyles };
  }, [data.metadata?.status, data.diffStatus]);

  const { onAction } = useNodeHandlers(data.nodeId ?? "", activeTabId);

  const handleCodeToggle = () => {
    nodeCode.toggleCode();
    data.onCodeToggle?.();
  };

  return (
    <div
      className={`relative min-w-[380px] max-w-[420px] overflow-hidden rounded-lg border-2 shadow-lg bg-white transition-all hover:shadow-xl ${
        selected ? "ring-4 ring-amber-400 ring-offset-1" : ""
      }`}
      style={{
        backgroundColor: statusStyles.backgroundColor || data.bgColor,
        color: statusStyles.color || data.textColor,
        borderColor: selected
          ? "#f59e0b"
          : statusStyles.borderColor || data.borderColor,
        ...statusStyles,
      }}
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
            iconColor={(statusStyles.color as string) || data.iconColor}
            borderColor={
              (statusStyles.borderColor as string) || data.borderColor
            }
            textColor={(statusStyles.color as string) || data.textColor}
            expandable={data.expandable}
            expanded={data.expanded}
            onToggle={data.onToggle}
            hasCode={Boolean(nodeCode.hasCode)}
            showCode={nodeCode.showCode}
            onCodeToggle={handleCodeToggle}
            status={data.metadata?.status}
            diffStatus={data.diffStatus as any}
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
            />
          ) : (
            <NodeDescription
              description={data.metadata?.description}
              textColor={data.textColor}
            />
          )}

          <NodeFooter
            createdAt={data.metadata?.createdAt}
            updatedAt={data.metadata?.updatedAt}
            textColor={(statusStyles.color as string) || data.textColor}
            borderColor={
              (statusStyles.borderColor as string) || data.borderColor
            }
            iconColor={(statusStyles.color as string) || data.iconColor}
          />
        </div>
      </NodeContextMenu>

      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
});

export default EnhancedNode;
