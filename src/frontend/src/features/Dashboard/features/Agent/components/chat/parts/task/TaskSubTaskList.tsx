import { SubTaskRow } from "./SubTaskRow";
import type { TaskSubWire } from "./types";

/** Fixed viewport; inner list scrolls when there are many sub-tasks. */
const SUB_LIST_HEIGHT = "h-40";

export function TaskSubTaskList({
  taskId,
  subTasks,
}: {
  taskId: string;
  subTasks: TaskSubWire[];
}) {
  if (subTasks.length === 0) return null;

  return (
    <div
      className={`${SUB_LIST_HEIGHT} space-y-2 overflow-y-auto overscroll-contain px-3 py-2.5 [scrollbar-gutter:stable]`}
    >
      {subTasks.map((sub, i) => (
        <SubTaskRow key={`${taskId}-sub-${i}`} sub={sub} />
      ))}
    </div>
  );
}
