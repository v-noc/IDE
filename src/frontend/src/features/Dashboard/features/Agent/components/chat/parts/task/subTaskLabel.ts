import type { TaskSubWire } from "./types";

export function subTaskLabel(sub: TaskSubWire): string {
  return sub.title ?? sub.name ?? "Sub-task";
}
