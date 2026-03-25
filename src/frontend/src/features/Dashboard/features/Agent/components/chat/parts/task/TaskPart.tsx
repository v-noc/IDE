import { useQuery } from "@tanstack/react-query";
import type { LucideIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";
import { useMemo, useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { isAgentPreviewTaskId } from "@/features/Dashboard/features/Agent/constants/agentPreviewConversation";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { cn } from "@/lib/utils";
import { agentTaskSubtasksQueryOptions } from "@/services/agent";
import { resolveTaskIcon } from "./taskIcons";
import { TaskStatusDot } from "./TaskStatusDot";
import { TaskSubTaskList } from "./TaskSubTaskList";
import { toVisualStatus } from "./taskStatus";
import type { TaskSubWire, TaskWirePart } from "./types";

function defaultExpanded(part: TaskWirePart): boolean {
  const main = toVisualStatus(part.state);
  if (main === "completed") return false;
  if (main === "error") return true;
  return true;
}

function TaskPartHeader({
  part,
  mainStatus,
  MainIcon,
  expandable,
  open,
}: {
  part: TaskWirePart;
  mainStatus: ReturnType<typeof toVisualStatus>;
  MainIcon: LucideIcon;
  expandable: boolean;
  open: boolean;
}) {
  const inner = (
    <>
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          mainStatus === "completed" &&
            "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
          mainStatus === "error" && "bg-destructive/10 text-destructive",
          mainStatus === "pending" && "bg-primary/10 text-primary",
        )}
      >
        <MainIcon className="h-4 w-4" strokeWidth={2} aria-hidden />
      </div>
      <div className="min-w-0 flex-1 text-left">
        <div className="flex items-start justify-between gap-2">
          <p className="text-[13px] font-semibold leading-tight tracking-tight text-foreground">
            {part.title}
          </p>
          <div className="flex shrink-0 items-center gap-1.5">
            {expandable ? (
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform duration-200",
                  open && "rotate-180",
                )}
                aria-hidden
              />
            ) : null}
            <TaskStatusDot status={mainStatus} />
          </div>
        </div>
        {part.description ? (
          <p className="mt-1 text-[11px] leading-snug text-muted-foreground">
            {part.description}
          </p>
        ) : null}
        {part.workflow_name ? (
          <p className="mt-1 font-mono text-[10px] text-muted-foreground/80">
            {part.workflow_name}
          </p>
        ) : null}
      </div>
    </>
  );

  if (expandable) {
    return (
      <CollapsibleTrigger
        className={cn(
          "flex w-full gap-3 border-b border-border/60 px-3 py-2.5 text-left outline-none",
          "hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        )}
      >
        {inner}
      </CollapsibleTrigger>
    );
  }

  return (
    <div className="flex gap-3 border-b border-border/60 px-3 py-2.5">
      {inner}
    </div>
  );
}

export function TaskPart({ part }: { part: TaskWirePart }) {
  const projectId = useProjectStore((s) => s.projectData?.id ?? "");
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const embeddedSubTasks: TaskSubWire[] = useMemo(
    () => part.sub_tasks ?? [],
    [part.sub_tasks],
  );
  const expectSubtasks = useMemo(
    () => embeddedSubTasks.length > 0 || (part.sub_task_count ?? 0) > 0,
    [embeddedSubTasks.length, part.sub_task_count],
  );

  const fetchEnabled =
    Boolean(projectId) && !isAgentPreviewTaskId(part.task_id);

  const subtasksQuery = useQuery(
    agentTaskSubtasksQueryOptions(
      projectId,
      part.task_id,
      branch,
      ref,
      compareTo,
      fetchEnabled,
    ),
  );

  const subTasks: TaskSubWire[] = useMemo(() => {
    const rows = subtasksQuery.data?.items;
    if (subtasksQuery.isSuccess && rows && rows.length > 0) {
      return rows;
    }
    return embeddedSubTasks;
  }, [embeddedSubTasks, subtasksQuery.data?.items, subtasksQuery.isSuccess]);

  const listLoading =
    fetchEnabled && subtasksQuery.isPending && embeddedSubTasks.length === 0;

  const MainIcon = resolveTaskIcon(part.icon);
  const mainStatus = toVisualStatus(part.state);
  const expandable = expectSubtasks || subTasks.length > 0;

  const [open, setOpen] = useState(() => defaultExpanded(part));

  if (!expandable) {
    return (
      <div className="overflow-hidden rounded-xl border border-border/80 bg-card text-card-foreground shadow-sm">
        <TaskPartHeader
          part={part}
          mainStatus={mainStatus}
          MainIcon={MainIcon}
          expandable={false}
          open={false}
        />
      </div>
    );
  }

  return (
    <Collapsible
      open={open}
      onOpenChange={setOpen}
      className="overflow-hidden rounded-xl border border-border/80 bg-card text-card-foreground shadow-sm"
    >
      <TaskPartHeader
        part={part}
        mainStatus={mainStatus}
        MainIcon={MainIcon}
        expandable
        open={open}
      />
      <CollapsibleContent>
        <TaskSubTaskList
          taskId={part.task_id}
          subTasks={subTasks}
          loading={listLoading}
        />
      </CollapsibleContent>
    </Collapsible>
  );
}
