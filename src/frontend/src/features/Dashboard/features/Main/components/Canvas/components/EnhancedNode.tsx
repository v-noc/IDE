import React, { useMemo, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import {
  ChevronDown,
  ChevronRight,
  Code2,
  Calendar,
  Copy,
  Check,
  Clock,
  Save,
} from "lucide-react";
import { format } from "date-fns";
import CodeEditor from "@/components/CodeEditor";
import { useEditorCode } from "@/features/Dashboard/features/Main/components/Code/useEditorCode";
import { useEditableCode } from "@/features/Dashboard/features/Main/components/Code/useEditableCode";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";

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

const formatDateTime = (dateString?: string): string => {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return format(date, "MMM d, yyyy 'at' h:mm a");
  } catch {
    return "N/A";
  }
};

const statusColor = (status: NodeMetadata["status"]): string => {
  switch (status) {
    case "error":
      return "#ef4444";
    case "warning":
      return "#f59e0b";
    case "success":
      return "#10b981";
    default:
      return "transparent";
  }
};

const EnhancedNode: React.FC<{ data: EnhancedNodeData }> = ({ data }) => {
  const [showCode, setShowCode] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const metadata = data.metadata || {};

  // Fetch code dynamically for the node
  const effectiveNodeId =
    data.nodeType === "call" && data.target
      ? data.target._key
      : data.nodeId || "";

  const { data: codeData } = useEditorCode(
    showCode ? effectiveNodeId : undefined
  );
  const {
    editorValue,
    hasChanges,
    isLoading: codeLoading,
    isError: codeError,
    isSaving,
    handleEditorChange,
    handleSave,
  } = useEditableCode(effectiveNodeId);

  const hasCode =
    (codeData?.code && codeData.code.length > 0) ||
    (metadata.code && metadata.code.length > 0) ||
    (editorValue && editorValue.length > 0);
  const displayCode = editorValue || codeData?.code || metadata.code || "";
  const fileName =
    codeData?.file_name || codeData?.file_path || metadata.fileName || "";
  const language = detectLanguage(fileName);

  const statusStyles = useMemo(() => {
    const color = statusColor(metadata.status);
    if (color === "transparent") return {};
    return {
      borderColor: color,
      boxShadow: `0 0 10px ${color}55`,
    };
  }, [metadata.status]);

  const handleCopyCode = (e: React.MouseEvent) => {
    e.stopPropagation();
    const codeToCopy = displayCode || metadata.code || "";
    if (!codeToCopy) return;
    navigator.clipboard.writeText(codeToCopy);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 1800);
  };

  const handleSaveClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    handleSave();
  };

  const handleToggleCode = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowCode((prev) => !prev);
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
      <div
        className="flex items-center gap-3 border-b px-4 py-3.5 bg-slate-50"
        style={{
          borderColor: data.borderColor,
        }}
      >
        {data.expandable ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              data.onToggle?.();
            }}
            title={data.expanded ? "Collapse" : "Expand"}
            className="flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all hover:scale-110 hover:shadow-md active:scale-95"
            style={{
              borderColor: data.borderColor,
              color: data.iconColor,
              backgroundColor: data.expanded ? data.iconColor : data.bgColor,
            }}
          >
            {data.expanded ? (
              <ChevronDown size={18} style={{ color: data.bgColor }} />
            ) : (
              <ChevronRight size={18} />
            )}
          </button>
        ) : null}

        <div className="flex items-center gap-2.5">
          <span className="text-xl" style={{ color: data.iconColor }}>
            {data.mainIcon}
          </span>
          <span className="text-base font-bold tracking-wide text-slate-800">
            {data.name}
          </span>
        </div>

        <div className="flex-1" />

        {metadata.status && metadata.status !== "idle" && (
          <span
            className="h-3 w-3 rounded-full ring-2 ring-white shadow-sm"
            style={{ backgroundColor: statusColor(metadata.status) }}
            title={`Status: ${metadata.status}`}
          />
        )}

        {hasCode && (
          <button
            onClick={handleToggleCode}
            title="Toggle code view"
            className="flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all hover:scale-110 hover:shadow-md active:scale-95"
            style={{
              borderColor: data.borderColor,
              backgroundColor: showCode ? data.iconColor : data.bgColor,
              color: showCode ? data.bgColor : data.iconColor,
            }}
          >
            <Code2 size={16} />
          </button>
        )}
      </div>

      {!showCode && (
        <div className="px-4 py-3.5 space-y-2.5 bg-white">
          {metadata.description ? (
            <p className="text-xs leading-relaxed text-slate-700">
              {metadata.description}
            </p>
          ) : (
            <div className="text-xs text-slate-400 italic">
              No description available
            </div>
          )}
        </div>
      )}

      {showCode && hasCode && (
        <div
          className="border-t bg-slate-50"
          style={{ borderColor: data.borderColor }}
        >
          <div
            className="flex items-center justify-between px-4 py-2.5 bg-white border-b"
            style={{ borderColor: data.borderColor }}
          >
            <span className="font-mono text-xs font-semibold text-slate-700">
              {fileName || metadata.language || "Code"}
            </span>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <button
                  onClick={handleSaveClick}
                  disabled={isSaving}
                  className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all hover:bg-slate-100 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ color: data.iconColor }}
                  title={isSaving ? "Saving..." : "Save changes"}
                >
                  <Save size={14} />
                  <span>{isSaving ? "Saving..." : "Save"}</span>
                </button>
              )}
              <button
                onClick={handleCopyCode}
                className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all hover:bg-slate-100 active:scale-95"
                style={{ color: data.iconColor }}
              >
                {copiedCode ? (
                  <>
                    <Check size={14} />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>
          <div
            className="h-[300px] mt-1 overflow-hidden border-b nodrag"
            style={{ borderColor: data.borderColor }}
          >
            <CodeEditor
              language={language}
              value={displayCode}
              onChange={handleEditorChange}
              isLoading={codeLoading}
              isError={codeError}
              options={{
                minimap: { enabled: false },
                readOnly: false,
                scrollBeyondLastLine: false,
                fontSize: 12,
                lineHeight: 18,
              }}
            />
          </div>
        </div>
      )}

      {/* Footer with created/updated dates */}
      {(metadata.createdAt || metadata.updatedAt) && (
        <div
          className="flex items-center justify-between gap-4 border-t px-4 py-2.5 text-[10px] bg-slate-50/50"
          style={{ borderColor: data.borderColor }}
        >
          {metadata.createdAt && (
            <div className="flex items-center gap-1.5 text-slate-500">
              <Calendar size={11} style={{ color: data.iconColor }} />
              <span className="font-medium">
                Created {formatDateTime(metadata.createdAt)}
              </span>
            </div>
          )}
          {metadata.updatedAt && (
            <div className="flex items-center gap-1.5 text-slate-500">
              <Clock size={11} style={{ color: data.iconColor }} />
              <span className="font-medium">
                Updated {formatDateTime(metadata.updatedAt)}
              </span>
            </div>
          )}
        </div>
      )}

      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
};

export default EnhancedNode;
