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

  const statusStyles = useMemo(() => {
    const status = data.metadata?.status;
    if (!status || status === "idle") return {};
    const colors: Record<string, string> = {
      error: "#ef4444",
      warning: "#f59e0b",
      success: "#10b981",
    };
    return {
      borderColor: colors[status],
      boxShadow: `0 0 10px ${colors[status]}55`,
    };
  }, [data.metadata?.status]);

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
        backgroundColor: data.bgColor,
        color: data.textColor,
        borderColor: selected ? "#f59e0b" : data.borderColor,
        ...statusStyles,
      }}
    >
      <NodeContextMenu
        nodeId={data.nodeId ?? ""}
        nodeType={data.nodeType ?? ""}
        manuallyCreated={data.manuallyCreated}
        onAction={onAction}
      >
        <NodeHeader
          name={data.name}
          icon={data.mainIcon}
          iconColor={data.iconColor}
          borderColor={data.borderColor}
          textColor={data.textColor}
          expandable={data.expandable}
          expanded={data.expanded}
          onToggle={data.onToggle}
          hasCode={Boolean(nodeCode.hasCode)}
          showCode={nodeCode.showCode}
          onCodeToggle={handleCodeToggle}
          status={data.metadata?.status}
        />
      </NodeContextMenu>

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
          borderColor={data.borderColor}
          iconColor={data.iconColor}
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
        textColor={data.textColor}
        borderColor={data.borderColor}
        iconColor={data.iconColor}
      />

      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
});

export default EnhancedNode;
