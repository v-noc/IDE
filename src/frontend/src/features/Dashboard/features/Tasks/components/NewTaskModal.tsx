import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { TaskType, TaskPriority, DependencySuggestion } from "@/types/tasks";
import { AnchorChip } from "./AnchorChip";
import { useCreateTask, useSuggestDependencies } from "../service/useTasks";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

interface NewTaskModalProps {
  projectId: string;
}

export function NewTaskModal({ projectId }: NewTaskModalProps) {
  const open = useProjectStore((s) => s.newTaskModalOpen);
  const preset = useProjectStore((s) => s.newTaskPreset);
  const closeNewTaskModal = useProjectStore((s) => s.closeNewTaskModal);

  const [title, setTitle] = useState("");
  const [taskType, setTaskType] = useState<TaskType>("task");
  const [priority, setPriority] = useState<TaskPriority>("none");
  const [description, setDescription] = useState("");
  const [anchorNodeId, setAnchorNodeId] = useState<string | null>(null);
  const [anchorQname, setAnchorQname] = useState("");
  const [anchorKind, setAnchorKind] = useState("function");
  const [checkedDeps, setCheckedDeps] = useState<Set<string>>(new Set());

  const createTask = useCreateTask(projectId);
  const { data: suggestions = [] } = useSuggestDependencies(
    projectId,
    anchorNodeId ?? undefined,
    open && !!anchorNodeId,
  );

  useEffect(() => {
    if (!open) return;
    setTitle("");
    setTaskType("task");
    setPriority("none");
    setDescription("");
    setCheckedDeps(new Set());
    if (preset?.anchorNodeId) {
      setAnchorNodeId(preset.anchorNodeId);
      setAnchorQname(preset.anchorQname ?? "");
      setAnchorKind(preset.anchorKind ?? "function");
    } else {
      setAnchorNodeId(null);
      setAnchorQname("");
    }
  }, [open, preset]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const created = await createTask.mutateAsync({
      title: title.trim(),
      task_type: taskType,
      priority,
      description,
      status: preset?.columnId,
      anchors: anchorNodeId ? [{ node_id: anchorNodeId }] : [],
    });

    const selected = suggestions.filter((s) => checkedDeps.has(s.node_id));
    for (const dep of selected) {
      await createTask.mutateAsync({
        title: dep.qname,
        task_type: "task",
        anchors: [{ node_id: dep.node_id }],
        subtask_of: created.id,
      });
    }

    closeNewTaskModal();
  };

  const toggleDep = (nodeId: string) => {
    setCheckedDeps((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && closeNewTaskModal()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New task</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {anchorNodeId && (
            <div className="flex flex-wrap items-center gap-2">
              <AnchorChip
                anchor={{
                  node_id: anchorNodeId,
                  qname: anchorQname,
                  kind: anchorKind,
                  is_resolved: true,
                }}
              />
              <button
                type="button"
                onClick={() => setAnchorNodeId(null)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Remove
              </button>
            </div>
          )}

          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Task title"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />

          <div className="grid grid-cols-2 gap-3">
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value as TaskType)}
              className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
            >
              <option value="task">Task</option>
              <option value="bug">Bug</option>
              <option value="improvement">Improvement</option>
              <option value="epic">Epic</option>
            </select>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
              className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
            >
              <option value="none">No priority</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            rows={3}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm resize-none"
          />

          {suggestions.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Suggested subtasks
              </p>
              <div className="max-h-40 space-y-1 overflow-y-auto">
                {suggestions.map((dep: DependencySuggestion) => (
                  <label
                    key={dep.node_id}
                    className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-muted/50"
                  >
                    <input
                      type="checkbox"
                      checked={checkedDeps.has(dep.node_id)}
                      onChange={() => toggleDep(dep.node_id)}
                    />
                    <span className="font-mono text-xs">{dep.qname}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={closeNewTaskModal}
              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || createTask.isPending}
              className="rounded-md bg-green-700 px-3 py-1.5 text-sm text-white hover:bg-green-600 disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
