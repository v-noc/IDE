import { useState } from "react";
import { useProgress } from "@/services/socket";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileText,
  Code,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProgressEventPayload } from "@/types/progress";

interface ProgressIndicatorProps {
  projectId: string | undefined;
}

function ProgressDetails({ progress }: { progress: ProgressEventPayload }) {
  const { files, entities, phase, status } = progress;
  const fileProgress =
    files.total > 0 ? (files.processed / files.total) * 100 : 0;
  const entityProgress =
    entities.total > 0 ? (entities.processed / entities.total) * 100 : 0;

  const getPhaseLabel = (phase: string) => {
    switch (phase) {
      case "collecting":
        return "Collecting Structure";
      case "analyzing":
        return "Analyzing Code";
      case "scanning":
        return "Scanning Files";
      case "complete":
        return "Complete";
      case "error":
        return "Error";
      default:
        return phase;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "text-blue-500";
      case "success":
        return "text-green-500";
      case "failed":
        return "text-red-500";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <div className="space-y-4">
      {/* Phase and Status */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Phase</span>
          <span className={cn("text-sm font-semibold", getStatusColor(status))}>
            {getPhaseLabel(phase)}
          </span>
        </div>
        {status === "failed" && progress.error_message && (
          <div className="text-xs text-red-500 bg-red-50 dark:bg-red-950 p-2 rounded">
            {progress.error_message}
          </div>
        )}
      </div>

      {/* File Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">Files</span>
          </div>
          <span className="text-muted-foreground">
            {files.processed} / {files.total}
          </span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${fileProgress}%` }}
          />
        </div>
        {files.current_path && (
          <div className="text-xs text-muted-foreground truncate">
            Current: {files.current_path}
          </div>
        )}
      </div>

      {/* Entity Progress */}
      {entities.total > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <Code className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">Functions & Classes</span>
            </div>
            <span className="text-muted-foreground">
              {entities.processed} / {entities.total}
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${entityProgress}%` }}
            />
          </div>
          {entities.current_qname && (
            <div className="text-xs text-muted-foreground truncate">
              Current: {entities.current_qname}
            </div>
          )}
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>Functions: {entities.functions_found}</span>
            <span>Classes: {entities.classes_found}</span>
          </div>
        </div>
      )}

      {/* Timestamp */}
      <div className="text-xs text-muted-foreground pt-2 border-t">
        Updated: {new Date(progress.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
}

export function ProgressIndicator({ projectId }: ProgressIndicatorProps) {
  const { progress, isProcessing } = useProgress(projectId);
  const [open, setOpen] = useState(false);

  if (!progress || (!isProcessing && progress.phase === "complete")) {
    return null;
  }

  const { files } = progress;
  const fileCount = `${files.processed}/${files.total}`;
  const hasProgress = files.total > 0;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
            "hover:bg-muted/50 border border-border",
            isProcessing &&
              "bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800",
          )}
        >
          {isProcessing ? (
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
          ) : progress.status === "success" ? (
            <CheckCircle2 className="h-3 w-3 text-green-500" />
          ) : progress.status === "failed" ? (
            <AlertCircle className="h-3 w-3 text-red-500" />
          ) : null}
          {hasProgress && (
            <span
              className={cn(isProcessing && "text-blue-700 dark:text-blue-300")}
            >
              {fileCount}
            </span>
          )}
          {progress.phase !== "idle" && (
            <span className="text-muted-foreground capitalize">
              {progress.phase}
            </span>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end" side="bottom">
        <div className="space-y-2">
          <h4 className="font-semibold text-sm">Processing Progress</h4>
          <ProgressDetails progress={progress} />
        </div>
      </PopoverContent>
    </Popover>
  );
}
