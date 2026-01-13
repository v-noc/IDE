import React, { memo, useMemo } from "react";
import { Handle, Position } from "@xyflow/react";
import { NodeHeader } from "./NodeHeader";
import { NodeDescription } from "./NodeDescription";
import { NodeCodeView } from "./NodeCodeView";
import { NodeFooter } from "./NodeFooter";
import { useNodeCode } from "./useNodeCode";

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
  target?: { _key: string };
  [key: string]: unknown;
}

const EnhancedNode = memo(
  function EnhancedNode({ data }: { data: EnhancedNodeData }) {
    const nodeCode = useNodeCode({
      nodeId: data.nodeId ?? "",
      targetKey: data.target?._key,
      nodeType: data.nodeType,
    });

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

    const handleCodeToggle = () => {
      nodeCode.toggleCode();
      data.onCodeToggle?.();
    };

    return (
      <div
        className="relative min-w-[380px] max-w-[420px] overflow-hidden rounded-lg border-2 shadow-lg bg-white transition-all hover:shadow-xl"
        style={{
          backgroundColor: data.bgColor,
          color: data.textColor,
          borderColor: data.borderColor,
          ...statusStyles,
        }}
      >
        <NodeHeader
          name={data.name}
          icon={data.mainIcon}
          iconColor={data.iconColor}
          borderColor={data.borderColor}
          bgColor={data.bgColor}
          expandable={data.expandable}
          expanded={data.expanded}
          onToggle={data.onToggle}
          hasCode={Boolean(nodeCode.hasCode)}
          showCode={nodeCode.showCode}
          onCodeToggle={handleCodeToggle}
          status={data.metadata?.status}
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
            borderColor={data.borderColor}
            iconColor={data.iconColor}
          />
        ) : (
          <NodeDescription description={data.metadata?.description} />
        )}

        <NodeFooter
          createdAt={data.metadata?.createdAt}
          updatedAt={data.metadata?.updatedAt}
          borderColor={data.borderColor}
          iconColor={data.iconColor}
        />

        <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
        <Handle
          type="source"
          position={Position.Right}
          style={{ opacity: 0 }}
        />
      </div>
    );
  },
  (prev, next) => {
    // Custom comparison to reduce re-renders
    return (
      prev.data.nodeId === next.data.nodeId &&
      prev.data.name === next.data.name &&
      prev.data.expanded === next.data.expanded &&
      prev.data.metadata?.status === next.data.metadata?.status &&
      prev.data.metadata?.updatedAt === next.data.metadata?.updatedAt
    );
  }
);

export default EnhancedNode;
