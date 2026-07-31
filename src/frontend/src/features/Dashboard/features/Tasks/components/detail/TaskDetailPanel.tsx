import { useEffect, useRef, useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import SelectNodeDialog from "@/features/Dashboard/components/SelectNodeDialog";
import type { AnyNodeTree } from "@/types/project";
import type { BoardColumn, DependencySuggestion, Task, TaskAnchor } from "@/types/tasks";
import {
  useTaskBoard,
  useAnchorSummary,
  useUpdateTask,
  useAddNote,
  useMoveAnchor,
  useMoveTask,
  useAddSubtask,
  useRemoveSubtask,
  useAddAnchor,
  useRemoveAnchor,
  useSuggestDependencies,
  findTaskInBoard,
} from "../../service/useTasks";
import { TaskTypeBadge } from "../TaskTypeBadge";
import {
  AMBER,
  BORDER,
  GREEN,
  KIND_ICON,
  PRIORITY_COLORS,
  SURFACE,
  TEXT,
} from "../../theme";
import { tasksApi } from "@/services/tasks";
import {
  columnTitle,
  firstDoneColumn,
  firstWorkflowColumn,
  formatActivityDate,
  formatShortDate,
  searchLinkableTasks,
  sortSubtasks,
} from "./detailUtils";

interface TaskDetailPanelProps {
  projectId: string;
  onNavigateToNode?: (nodeId: string) => void;
}

const sectionHeading: React.CSSProperties = {
  fontSize: 10.5,
  fontWeight: 700,
  letterSpacing: "0.08em",
  color: TEXT.label,
  textTransform: "uppercase",
};

export function TaskDetailPanel({
  projectId,
  onNavigateToNode,
}: TaskDetailPanelProps) {
  const selectedTaskId = useProjectStore((s) => s.selectedTaskId);
  const setSelectedTaskId = useProjectStore((s) => s.setSelectedTaskId);
  const projectData = useProjectStore((s) => s.projectData);

  const { data: board } = useTaskBoard(projectId);
  const { data: anchorSummary } = useAnchorSummary(projectId);
  const updateTask = useUpdateTask(projectId);
  const addNote = useAddNote(projectId);
  const moveAnchor = useMoveAnchor(projectId);
  const moveTask = useMoveTask(projectId);
  const addSubtask = useAddSubtask(projectId);
  const removeSubtask = useRemoveSubtask(projectId);
  const addAnchor = useAddAnchor(projectId);
  const removeAnchor = useRemoveAnchor(projectId);

  const [navStack, setNavStack] = useState<string[]>([]);
  const [noteText, setNoteText] = useState("");
  const [reAnchorNodeId, setReAnchorNodeId] = useState<string | null>(null);
  const [reAnchorMeta, setReAnchorMeta] = useState<{ qname: string; kind?: string }>({
    qname: "",
  });
  const [addAnchorOpen, setAddAnchorOpen] = useState(false);
  const [editingDescription, setEditingDescription] = useState(false);
  const [descriptionDraft, setDescriptionDraft] = useState("");
  const [addingSubtask, setAddingSubtask] = useState(false);
  const [subtaskQuery, setSubtaskQuery] = useState("");
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [checkedDeps, setCheckedDeps] = useState<Set<string>>(new Set());

  const titleRef = useRef<HTMLInputElement>(null);
  const savedTitleRef = useRef("");

  const task = findTaskInBoard(board, selectedTaskId);
  const columns = board?.board.columns ?? [];
  const doneColumnIds = new Set(columns.filter((c) => c.is_done).map((c) => c.id));

  const firstResolvedAnchor = task?.anchors.find((a) => a.is_resolved !== false);
  const { data: suggestions = [] } = useSuggestDependencies(
    projectId,
    firstResolvedAnchor?.node_id,
    suggestOpen && !!firstResolvedAnchor,
  );

  useEffect(() => {
    if (task) {
      savedTitleRef.current = task.title;
      setDescriptionDraft(task.description);
      setEditingDescription(false);
    }
  }, [task?.id, task?.title, task?.description]);

  if (!task) return null;

  const handleClose = () => {
    setSelectedTaskId(null);
    setNavStack([]);
  };

  const handleBack = () => {
    const prev = navStack[navStack.length - 1];
    if (prev) {
      setNavStack((s) => s.slice(0, -1));
      setSelectedTaskId(prev);
    } else {
      handleClose();
    }
  };

  const navigateToTask = (taskId: string) => {
    if (selectedTaskId) {
      setNavStack((s) => [...s, selectedTaskId]);
    }
    setSelectedTaskId(taskId);
  };

  const commitTitle = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) {
      if (titleRef.current) titleRef.current.value = savedTitleRef.current;
      return;
    }
    if (trimmed !== savedTitleRef.current) {
      updateTask.mutate({ taskId: task.id, payload: { title: trimmed } });
      savedTitleRef.current = trimmed;
    }
  };

  const commitDescription = () => {
    setEditingDescription(false);
    if (descriptionDraft !== task.description) {
      updateTask.mutate({
        taskId: task.id,
        payload: { description: descriptionDraft },
      });
    }
  };

  const toggleSubtaskDone = (sub: Task["subtasks"][number]) => {
    const doneCol = firstDoneColumn(columns);
    const workflowCol = firstWorkflowColumn(columns);
    if (!doneCol || !workflowCol) return;
    const child = board?.tasks.find((t) => t.id === sub.id);
    const isDone = doneColumnIds.has(sub.status);
    const targetStatus = isDone ? workflowCol.id : doneCol.id;
    moveTask.mutate({
      taskId: sub.id,
      payload: { status: targetStatus, rank: child?.rank ?? "U" },
    });
  };

  const sortedSubtasks = sortSubtasks(task.subtasks, columns, doneColumnIds);

  const openSuggest = () => {
    setCheckedDeps(new Set());
    setSuggestOpen(true);
  };

  const applySuggestions = async () => {
    const selected = suggestions.filter((s) => checkedDeps.has(s.node_id));
    for (const dep of selected) {
      await addSubtask.mutateAsync({
        parentId: task.id,
        payload: {
          title: dep.qname,
          anchors: [{ node_id: dep.node_id }],
        },
      });
    }
    setSuggestOpen(false);
  };

  return (
    <div
      className="relative flex h-full w-full min-w-0 flex-col overflow-hidden"
      style={{
        borderLeft: `1px solid ${BORDER.panel}`,
        backgroundColor: SURFACE.panel,
      }}
    >
      {/* Header */}
      <div
        className="flex w-full min-w-0 shrink-0 items-center gap-2"
        style={{
          height: 44,
          padding: "0 12px 0 16px",
          borderBottom: `1px solid ${BORDER.row}`,
        }}
      >
        {navStack.length > 0 && (
          <button
            type="button"
            onClick={handleBack}
            style={{ color: TEXT.dim }}
            className="shrink-0 hover:opacity-80"
          >
            ←
          </button>
        )}
        <div className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
          <TaskTypeBadge type={task.task_type} className="shrink-0" />
          <span
            className="truncate font-mono"
            style={{ fontSize: 10.5, color: TEXT.faint }}
          >
            {task.key}
          </span>
        </div>
        <button
          type="button"
          onClick={handleClose}
          className="shrink-0 rounded-md px-1.5 py-0.5 hover:bg-[#22252b]"
          style={{ color: TEXT.dim, fontSize: 15 }}
          aria-label="Close task panel"
        >
          ✕
        </button>
      </div>

      <div
        className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden"
        style={{ padding: 16, display: "flex", flexDirection: "column", gap: 18 }}
      >
        {/* 1 · Title */}
        <input
          key={task.id}
          ref={titleRef}
          defaultValue={task.title}
          onBlur={(e) => commitTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.currentTarget.blur();
            }
            if (e.key === "Escape") {
              e.currentTarget.value = savedTitleRef.current;
              e.currentTarget.blur();
            }
          }}
          className="w-full rounded-lg border border-transparent bg-transparent font-semibold outline-none hover:border-[#26292f] focus:border-[#3ecf72] focus:bg-[#15161a]"
          style={{
            fontSize: 16.5,
            fontWeight: 650,
            color: TEXT.bright,
            padding: "6px 8px",
            margin: "-6px -8px 0",
          }}
        />

        {/* 2 · Fields grid */}
        <FieldsGrid task={task} columns={columns} />

        {/* 3 · Labels */}
        {task.labels.length > 0 && (
          <div className="flex flex-wrap gap-1.5" style={{ marginTop: -8 }}>
            {task.labels.map((label) => (
              <span
                key={label}
                style={{
                  fontSize: 10.5,
                  fontWeight: 550,
                  color: TEXT.muted,
                  backgroundColor: SURFACE.chip,
                  border: `1px solid ${BORDER.chip}`,
                  borderRadius: 99,
                  padding: "3px 9px",
                }}
              >
                {label}
              </span>
            ))}
          </div>
        )}

        {/* 4 · Description */}
        <div>
          <p style={sectionHeading} className="mb-2">
            Description
          </p>
          {editingDescription ? (
            <textarea
              autoFocus
              value={descriptionDraft}
              onChange={(e) => setDescriptionDraft(e.target.value)}
              onBlur={commitDescription}
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  setDescriptionDraft(task.description);
                  setEditingDescription(false);
                }
              }}
              className="w-full resize-none rounded-lg outline-none focus:border-[#3ecf72]"
              style={{
                fontSize: 12.5,
                lineHeight: 1.65,
                color: TEXT.body,
                backgroundColor: SURFACE.input,
                border: `1px solid ${GREEN.core}`,
                borderRadius: 9,
                padding: "11px 13px",
                minHeight: 80,
              }}
            />
          ) : (
            <button
              type="button"
              onClick={() => setEditingDescription(true)}
              className="w-full text-left rounded-lg"
              style={{
                fontSize: 12.5,
                lineHeight: 1.65,
                color: task.description ? TEXT.body : TEXT.faint,
                backgroundColor: SURFACE.input,
                border: `1px solid ${BORDER.input}`,
                borderRadius: 9,
                padding: "11px 13px",
              }}
            >
              {task.description || "Add a description…"}
            </button>
          )}
        </div>

        {/* 5 · Anchored nodes */}
        <AnchorsSection
          task={task}
          anchorSummary={anchorSummary}
          onNavigateToNode={onNavigateToNode}
          onReAnchor={(anchor) => {
            setReAnchorNodeId(anchor.node_id);
            setReAnchorMeta({ qname: anchor.qname, kind: anchor.kind });
          }}
          onRemove={(nodeId) =>
            removeAnchor.mutate({ taskId: task.id, nodeId })
          }
          onAdd={() => setAddAnchorOpen(true)}
        />

        {/* 6 · Subtasks */}
        <SubtasksSection
          task={task}
          sortedSubtasks={sortedSubtasks}
          columns={columns}
          doneColumnIds={doneColumnIds}
          addingSubtask={addingSubtask}
          subtaskQuery={subtaskQuery}
          boardTasks={board?.tasks ?? []}
          onToggleDone={toggleSubtaskDone}
          onNavigate={navigateToTask}
          onUnlink={(childId) =>
            removeSubtask.mutate({ parentId: task.id, childId })
          }
          onStartAdd={() => {
            setAddingSubtask(true);
            setSubtaskQuery("");
          }}
          onSubtaskQueryChange={setSubtaskQuery}
          onCancelAdd={() => {
            setAddingSubtask(false);
            setSubtaskQuery("");
          }}
          onLinkExisting={(childId) => {
            addSubtask.mutate(
              { parentId: task.id, payload: { child_id: childId } },
              {
                onSuccess: () => {
                  setAddingSubtask(false);
                  setSubtaskQuery("");
                },
              },
            );
          }}
          onCreateInline={(title) => {
            addSubtask.mutate(
              { parentId: task.id, payload: { title } },
              {
                onSuccess: () => {
                  setAddingSubtask(false);
                  setSubtaskQuery("");
                },
              },
            );
          }}
          onSuggest={openSuggest}
        />

        {/* 7 · Dependencies */}
        {(task.blocked_by.length > 0 || task.blocks.length > 0) && (
          <DependenciesSection
            task={task}
            columns={columns}
            boardTasks={board?.tasks ?? []}
            onNavigate={navigateToTask}
          />
        )}

        {/* 8 · Activity */}
        <ActivitySection
          notes={task.notes}
          noteText={noteText}
          onNoteTextChange={setNoteText}
          onSubmitNote={() => {
            if (!noteText.trim()) return;
            addNote.mutate({ taskId: task.id, text: noteText.trim() });
            setNoteText("");
          }}
        />
      </div>

      {reAnchorNodeId && (
        <ReAnchorPicker
          projectId={projectId}
          qname={reAnchorMeta.qname}
          kind={reAnchorMeta.kind}
          onSelect={(nodeId) => {
            moveAnchor.mutate({
              taskId: task.id,
              fromNodeId: reAnchorNodeId,
              toNodeId: nodeId,
            });
            setReAnchorNodeId(null);
          }}
          onClose={() => setReAnchorNodeId(null)}
        />
      )}

      {addAnchorOpen && projectData && (
        <SelectNodeDialog
          isOpen
          onClose={() => setAddAnchorOpen(false)}
          list={(projectData.children as AnyNodeTree[]) ?? []}
          selectNodeType={["function", "class", "file", "folder"]}
          onSelect={(node) => {
            addAnchor.mutate({ taskId: task.id, nodeId: node.id });
            setAddAnchorOpen(false);
          }}
        />
      )}

      {suggestOpen && (
        <SuggestDependenciesDialog
          suggestions={suggestions}
          checked={checkedDeps}
          onToggle={(id) => {
            setCheckedDeps((prev) => {
              const next = new Set(prev);
              if (next.has(id)) next.delete(id);
              else next.add(id);
              return next;
            });
          }}
          onApply={applySuggestions}
          onClose={() => setSuggestOpen(false)}
        />
      )}
    </div>
  );
}

function FieldsGrid({ task, columns }: { task: Task; columns: BoardColumn[] }) {
  const column = columns.find((c) => c.id === task.status);
  return (
    <div className="grid grid-cols-2 gap-2">
      {[
        {
          label: "Status",
          value: (
            <span className="flex items-center gap-1.5" style={{ color: TEXT.heading }}>
              <span
                className="inline-block rounded-full"
                style={{
                  width: 7,
                  height: 7,
                  backgroundColor: column?.color ?? TEXT.faint,
                }}
              />
              {column?.title ?? task.status}
            </span>
          ),
        },
        {
          label: "Priority",
          value: (
            <span
              style={{
                color:
                  task.priority === "none"
                    ? TEXT.label
                    : PRIORITY_COLORS[task.priority],
              }}
            >
              {task.priority}
            </span>
          ),
        },
        {
          label: "Created",
          value: (
            <span style={{ color: TEXT.muted }}>{formatShortDate(task.created_at)}</span>
          ),
        },
        {
          label: "Updated",
          value: (
            <span style={{ color: TEXT.muted }}>{formatShortDate(task.updated_at)}</span>
          ),
        },
      ].map((field) => (
        <div
          key={field.label}
          style={{
            backgroundColor: SURFACE.input,
            border: `1px solid ${BORDER.input}`,
            borderRadius: 8,
            padding: "8px 10px",
          }}
        >
          <p
            style={{
              fontSize: 9.5,
              fontWeight: 700,
              letterSpacing: "0.07em",
              color: TEXT.label,
              marginBottom: 4,
            }}
          >
            {field.label}
          </p>
          <div style={{ fontSize: 12.5, fontWeight: 550 }}>{field.value}</div>
        </div>
      ))}
    </div>
  );
}

function KindGlyph({ kind }: { kind: string }) {
  const icon = KIND_ICON[kind] ?? KIND_ICON.function;
  return (
    <span
      className="inline-flex w-[13px] shrink-0 justify-center font-mono"
      style={{ fontSize: 10, color: icon.color }}
    >
      {icon.glyph}
    </span>
  );
}

function AnchorsSection({
  task,
  anchorSummary,
  onNavigateToNode,
  onReAnchor,
  onRemove,
  onAdd,
}: {
  task: Task;
  anchorSummary: ReturnType<typeof useAnchorSummary>["data"];
  onNavigateToNode?: (nodeId: string) => void;
  onReAnchor: (anchor: TaskAnchor) => void;
  onRemove: (nodeId: string) => void;
  onAdd: () => void;
}) {
  return (
    <div>
      <p style={sectionHeading} className="mb-2">
        Anchored nodes
      </p>
      <div
        style={{
          border: `1px solid ${BORDER.panel}`,
          borderRadius: 9,
          overflow: "hidden",
        }}
      >
        {task.anchors.length === 0 ? (
          <div
            style={{
              padding: "9px 12px",
              color: TEXT.faint,
              fontSize: 12,
            }}
          >
            No anchored nodes
          </div>
        ) : (
          task.anchors.map((anchor, index) => {
            const summary = anchorSummary?.nodes[anchor.node_id];
            const unresolved = anchor.is_resolved === false;
            return (
              <div
                key={`${anchor.node_id}-${index}`}
                className="group flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1.5"
                style={{
                  padding: "9px 12px",
                  borderBottom:
                    index < task.anchors.length - 1
                      ? `1px solid ${BORDER.row}`
                      : undefined,
                  backgroundColor: unresolved ? AMBER.rowBg : undefined,
                }}
              >
                <KindGlyph kind={anchor.kind} />
                <span
                  className="min-w-0 flex-1 truncate font-mono"
                  style={{ fontSize: 12, color: TEXT.heading }}
                >
                  {anchor.qname}
                </span>
                {summary?.hot && (
                  <span
                    style={{
                      fontSize: 9.5,
                      fontWeight: 650,
                      color: AMBER.text,
                      backgroundColor: AMBER.bg,
                      border: `1px solid rgba(226,160,63,.3)`,
                      borderRadius: 99,
                      padding: "2px 7px",
                    }}
                  >
                    hot · {summary.open_count} tasks
                  </span>
                )}
                {unresolved && (
                  <span style={{ fontSize: 9.5, fontWeight: 650, color: AMBER.core }}>
                    ⚠ unresolved
                  </span>
                )}
                <div className="ml-auto flex shrink-0 items-center gap-1.5">
                  {unresolved ? (
                    <button
                      type="button"
                      onClick={() => onReAnchor(anchor)}
                      className="whitespace-nowrap"
                      style={{
                        fontSize: 10.5,
                        fontWeight: 600,
                        color: AMBER.text,
                        backgroundColor: AMBER.bg,
                        border: `1px solid ${AMBER.border}`,
                        borderRadius: 6,
                        padding: "3px 9px",
                      }}
                    >
                      Re-anchor
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => onNavigateToNode?.(anchor.node_id)}
                      className="whitespace-nowrap"
                      style={{
                        fontSize: 10.5,
                        color: TEXT.muted,
                        backgroundColor: "#1f2126",
                        border: `1px solid ${BORDER.chip}`,
                        borderRadius: 6,
                        padding: "3px 9px",
                      }}
                    >
                      Show on canvas
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => onRemove(anchor.node_id)}
                    className="opacity-0 group-hover:opacity-100"
                    style={{ fontSize: 12, color: TEXT.dim }}
                    title="Unlink anchor"
                  >
                    ✕
                  </button>
                </div>
              </div>
            );
          })
        )}
        <button
          type="button"
          onClick={onAdd}
          className="w-full text-left"
          style={{
            padding: "8px 12px",
            fontSize: 11.5,
            color: TEXT.dim,
            borderTop: task.anchors.length ? `1px solid ${BORDER.row}` : undefined,
          }}
        >
          + Add anchor
        </button>
      </div>
    </div>
  );
}

function SubtasksSection({
  task,
  sortedSubtasks,
  columns,
  doneColumnIds,
  addingSubtask,
  subtaskQuery,
  boardTasks,
  onToggleDone,
  onNavigate,
  onUnlink,
  onStartAdd,
  onSubtaskQueryChange,
  onCancelAdd,
  onLinkExisting,
  onCreateInline,
  onSuggest,
}: {
  task: Task;
  sortedSubtasks: Task["subtasks"];
  columns: BoardColumn[];
  doneColumnIds: Set<string>;
  addingSubtask: boolean;
  subtaskQuery: string;
  boardTasks: Task[];
  onToggleDone: (sub: Task["subtasks"][number]) => void;
  onNavigate: (id: string) => void;
  onUnlink: (childId: string) => void;
  onStartAdd: () => void;
  onSubtaskQueryChange: (q: string) => void;
  onCancelAdd: () => void;
  onLinkExisting: (childId: string) => void;
  onCreateInline: (title: string) => void;
  onSuggest: () => void;
}) {
  const matches = searchLinkableTasks(boardTasks, task, subtaskQuery).slice(0, 8);

  return (
    <div>
      <p style={sectionHeading} className="mb-2">
        Subtasks · {task.subtask_progress.done}/{task.subtask_progress.total}
      </p>
      {sortedSubtasks.length > 0 && (
        <div
          style={{
            border: `1px solid ${BORDER.panel}`,
            borderRadius: 9,
            overflow: "hidden",
            marginBottom: 8,
          }}
        >
          {sortedSubtasks.map((sub, index) => {
            const isDone = doneColumnIds.has(sub.status);
            return (
              <div
                key={sub.id}
                className="group flex items-center gap-2 hover:bg-[#17191d]"
                style={{
                  padding: "8px 12px",
                  gap: 9,
                  borderBottom:
                    index < sortedSubtasks.length - 1
                      ? `1px solid ${BORDER.row}`
                      : undefined,
                }}
              >
                <button
                  type="button"
                  onClick={() => onToggleDone(sub)}
                  className="flex shrink-0 items-center justify-center"
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: 5,
                    fontSize: 10,
                    backgroundColor: isDone ? GREEN.btn : "#1a1c21",
                    border: `1px solid ${isDone ? GREEN.btnBorder : BORDER.strong}`,
                    color: isDone ? "#0b1a10" : "transparent",
                  }}
                >
                  {isDone ? "✓" : ""}
                </button>
                <button
                  type="button"
                  onClick={() => onNavigate(sub.id)}
                  className="min-w-0 flex-1 truncate text-left hover:text-[#7fdba3]"
                  style={{
                    fontSize: 12.5,
                    fontWeight: 550,
                    color: isDone ? TEXT.label : TEXT.heading,
                    textDecoration: isDone ? "line-through" : undefined,
                  }}
                >
                  {sub.title}
                </button>
                {sub.shared && (
                  <span
                    title="Shared — has multiple parent tasks"
                    style={{
                      fontSize: 9.5,
                      fontWeight: 600,
                      color: "#a78bfa",
                      backgroundColor: "rgba(167,139,250,.09)",
                      border: "rgba(167,139,250,.28) 1px solid",
                      borderRadius: 99,
                      padding: "2px 6px",
                    }}
                  >
                    ⑂ shared
                  </span>
                )}
                <span
                  className="font-mono shrink-0"
                  style={{ fontSize: 9.5, color: TEXT.faint }}
                >
                  {columnTitle(columns, sub.status)}
                </span>
                <button
                  type="button"
                  onClick={() => onUnlink(sub.id)}
                  className="opacity-0 group-hover:opacity-100"
                  style={{ fontSize: 12, color: TEXT.dim }}
                  title="Unlink subtask"
                >
                  ✕
                </button>
              </div>
            );
          })}
        </div>
      )}

      {addingSubtask && (
        <div className="relative mb-2">
          <input
            autoFocus
            value={subtaskQuery}
            onChange={(e) => onSubtaskQueryChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape") onCancelAdd();
              if (e.key === "Enter") {
                const trimmed = subtaskQuery.trim();
                if (!trimmed) return;
                const exact = matches.find(
                  (t) =>
                    t.title.toLowerCase() === trimmed.toLowerCase() ||
                    t.key.toLowerCase() === trimmed.toLowerCase(),
                );
                if (exact) onLinkExisting(exact.id);
                else onCreateInline(trimmed);
              }
            }}
            placeholder="Search or name a subtask…"
            className="w-full rounded-lg outline-none focus:border-[#3ecf72]"
            style={{
              fontSize: 12,
              padding: "8px 11px",
              backgroundColor: SURFACE.input,
              border: `1px solid ${BORDER.input}`,
              color: TEXT.heading,
            }}
          />
          {subtaskQuery.trim() && matches.length > 0 && (
            <div
              className="absolute left-0 right-0 z-10 mt-1 overflow-hidden rounded-lg shadow-lg"
              style={{
                backgroundColor: SURFACE.input,
                border: `1px solid ${BORDER.chip}`,
              }}
            >
              {matches.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onLinkExisting(t.id)}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-[#1c1e23]"
                >
                  <span className="font-mono text-[10px]" style={{ color: TEXT.faint }}>
                    {t.key}
                  </span>
                  <span style={{ fontSize: 12, color: TEXT.heading }}>{t.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onStartAdd}
          style={{
            fontSize: 11.5,
            color: TEXT.dim,
            border: `1px dashed ${BORDER.chip}`,
            borderRadius: 7,
            padding: "6px 11px",
          }}
        >
          + Add subtask
        </button>
        <button
          type="button"
          onClick={onSuggest}
          disabled={!task.anchors.some((a) => a.is_resolved !== false)}
          style={{
            fontSize: 11.5,
            color: GREEN.link,
            border: "1px dashed rgba(62,207,114,.3)",
            borderRadius: 7,
            padding: "6px 11px",
            opacity: task.anchors.some((a) => a.is_resolved !== false) ? 1 : 0.5,
          }}
        >
          ✦ Suggest from dependencies
        </button>
      </div>
    </div>
  );
}

function DependenciesSection({
  task,
  columns,
  boardTasks,
  onNavigate,
}: {
  task: Task;
  columns: BoardColumn[];
  boardTasks: Task[];
  onNavigate: (id: string) => void;
}) {
  const typeById = new Map(boardTasks.map((t) => [t.id, t.task_type]));
  const rows = [
    ...task.blocked_by.map((r) => ({ ...r, direction: "blocked by" as const })),
    ...task.blocks.map((r) => ({ ...r, direction: "blocks" as const })),
  ];

  return (
    <div>
      <p style={sectionHeading} className="mb-2">
        Dependencies
      </p>
      <div className="flex flex-col gap-1.5">
        {rows.map((row) => (
          <button
            key={`${row.direction}-${row.id}`}
            type="button"
            onClick={() => onNavigate(row.id)}
            className="flex w-full items-center gap-2 rounded-lg text-left hover:border-[#33373f]"
            style={{
              backgroundColor: SURFACE.input,
              border: `1px solid ${BORDER.input}`,
              borderRadius: 8,
              padding: "8px 11px",
            }}
          >
            <span
              style={{
                fontSize: 10,
                fontWeight: 650,
                minWidth: 70,
                color: row.direction === "blocked by" ? "#e07a7a" : AMBER.core,
              }}
            >
              {row.direction}
            </span>
            <TaskTypeBadge
              type={typeById.get(row.id) ?? "task"}
              className="!text-[9px]"
            />
            <span
              className="flex-1 truncate"
              style={{ fontSize: 12, fontWeight: 550, color: TEXT.bright }}
            >
              {row.title}
            </span>
            <span className="font-mono" style={{ fontSize: 9.5, color: TEXT.dim }}>
              {columnTitle(columns, row.status)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ActivitySection({
  notes,
  noteText,
  onNoteTextChange,
  onSubmitNote,
}: {
  notes: Task["notes"];
  noteText: string;
  onNoteTextChange: (v: string) => void;
  onSubmitNote: () => void;
}) {
  return (
    <div>
      <p style={sectionHeading} className="mb-2">
        Activity
      </p>
      {notes.length > 0 && (
        <div className="mb-3 flex flex-col gap-2">
          {notes.map((note, i) => (
            <div key={i} className="flex gap-2" style={{ fontSize: 11.5, lineHeight: 1.5 }}>
              <span
                className="mt-1 shrink-0 rounded-full"
                style={{ width: 6, height: 6, backgroundColor: BORDER.chip }}
              />
              <p style={{ color: TEXT.dim }}>
                {note.text}{" "}
                <span className="font-mono" style={{ fontSize: 10, color: TEXT.faint }}>
                  {formatActivityDate(note.at)}
                </span>
              </p>
            </div>
          ))}
        </div>
      )}
      <input
        value={noteText}
        onChange={(e) => onNoteTextChange(e.target.value)}
        placeholder="Add a note…"
        onKeyDown={(e) => {
          if (e.key === "Enter") onSubmitNote();
        }}
        className="w-full rounded-lg outline-none focus:border-[#3ecf72]"
        style={{
          backgroundColor: SURFACE.input,
          border: `1px solid ${BORDER.input}`,
          borderRadius: 8,
          padding: "8px 11px",
          fontSize: 12,
          color: TEXT.heading,
        }}
      />
    </div>
  );
}

function ReAnchorPicker({
  projectId,
  qname,
  kind,
  onSelect,
  onClose,
}: {
  projectId: string;
  qname: string;
  kind?: string;
  onSelect: (nodeId: string) => void;
  onClose: () => void;
}) {
  const [candidates, setCandidates] = useState<
    Array<{ node_id: string; qname: string; kind: string }>
  >([]);

  useEffect(() => {
    tasksApi.reAnchorCandidates(projectId, qname, kind).then(setCandidates);
  }, [projectId, qname, kind]);

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="w-80 rounded-lg p-4 shadow-lg"
        style={{ backgroundColor: SURFACE.panel, border: `1px solid ${BORDER.chip}` }}
      >
        <p className="mb-2 text-sm font-medium" style={{ color: TEXT.heading }}>
          Re-anchor
        </p>
        <div className="max-h-48 space-y-1 overflow-y-auto">
          {candidates.map((c) => (
            <button
              key={c.node_id}
              type="button"
              onClick={() => onSelect(c.node_id)}
              className="block w-full rounded px-2 py-1 text-left font-mono hover:bg-[#1c1e23]"
              style={{ fontSize: 12, color: TEXT.heading }}
            >
              {c.qname}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="mt-3"
          style={{ fontSize: 12, color: TEXT.dim }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function SuggestDependenciesDialog({
  suggestions,
  checked,
  onToggle,
  onApply,
  onClose,
}: {
  suggestions: DependencySuggestion[];
  checked: Set<string>;
  onToggle: (id: string) => void;
  onApply: () => void;
  onClose: () => void;
}) {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="w-96 rounded-lg p-4 shadow-lg"
        style={{ backgroundColor: SURFACE.panel, border: `1px solid ${BORDER.chip}` }}
      >
        <p className="mb-2 text-sm font-medium" style={{ color: TEXT.heading }}>
          Suggest from dependencies
        </p>
        {suggestions.length === 0 ? (
          <p style={{ fontSize: 12, color: TEXT.faint }}>no dependencies found</p>
        ) : (
          <div className="max-h-56 space-y-1 overflow-y-auto">
            {suggestions.map((s) => (
              <label
                key={s.node_id}
                className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-[#1c1e23]"
              >
                <input
                  type="checkbox"
                  checked={checked.has(s.node_id)}
                  onChange={() => onToggle(s.node_id)}
                />
                <KindGlyph kind={s.kind} />
                <span className="font-mono" style={{ fontSize: 12, color: TEXT.heading }}>
                  {s.qname || s.node_id}
                </span>
              </label>
            ))}
          </div>
        )}
        <div className="mt-3 flex justify-end gap-2">
          <button type="button" onClick={onClose} style={{ fontSize: 12, color: TEXT.dim }}>
            Cancel
          </button>
          {suggestions.length > 0 && (
            <button
              type="button"
              onClick={onApply}
              style={{ fontSize: 12, color: GREEN.link }}
            >
              Add selected
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
