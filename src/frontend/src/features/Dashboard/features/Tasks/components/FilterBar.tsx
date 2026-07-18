import { useEffect, useEffectEvent, useRef } from "react";
import type { TaskFilters, TaskType, TaskView } from "@/types/tasks";

const TYPE_OPTIONS: Array<{ value: TaskType | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "bug", label: "Bug" },
  { value: "task", label: "Task" },
  { value: "improvement", label: "Improvement" },
  { value: "epic", label: "Epic" },
];

const VIEW_OPTIONS: Array<{ value: TaskView; label: string }> = [
  { value: "board", label: "Board" },
  { value: "list", label: "List" },
];

interface FilterBarProps {
  view: TaskView;
  filters: TaskFilters;
  openCount: number;
  hotCount: number;
  onViewChange: (view: TaskView) => void;
  onFiltersChange: (filters: Partial<TaskFilters>) => void;
  onNewTask: () => void;
}

export function FilterBar({
  view,
  filters,
  openCount,
  hotCount,
  onViewChange,
  onFiltersChange,
  onNewTask,
}: FilterBarProps) {
  const searchRef = useRef<HTMLInputElement>(null);

  const onSearchKeyDown = useEffectEvent((e: KeyboardEvent) => {
    const target = e.target as HTMLElement | null;
    const inInput =
      target?.tagName === "INPUT" ||
      target?.tagName === "TEXTAREA" ||
      target?.isContentEditable;

    if (e.key === "/" && !inInput) {
      e.preventDefault();
      searchRef.current?.focus();
    }
    if (e.key === "Escape" && document.activeElement === searchRef.current) {
      onFiltersChange({ query: "" });
      searchRef.current?.blur();
    }
  });

  useEffect(() => {
    window.addEventListener("keydown", onSearchKeyDown);
    return () => window.removeEventListener("keydown", onSearchKeyDown);
  }, [onSearchKeyDown]);

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
      <div className="flex rounded-md border border-border overflow-hidden">
        {VIEW_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onViewChange(opt.value)}
            className={[
              "px-2.5 py-1 text-xs transition-colors",
              view === opt.value
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:text-foreground",
            ].join(" ")}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <input
        ref={searchRef}
        type="text"
        placeholder="Search tasks…  ( / )"
        value={filters.query}
        onChange={(e) => onFiltersChange({ query: e.target.value })}
        className="h-8 w-52 rounded-md border border-border bg-background px-2 text-xs"
      />

      <div className="flex rounded-md border border-border overflow-hidden">
        {TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onFiltersChange({ type: opt.value })}
            className={[
              "px-2.5 py-1 text-xs transition-colors",
              filters.type === opt.value
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:text-foreground",
            ].join(" ")}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="flex-1" />

      <span className="text-xs text-muted-foreground">
        {openCount} open
        {hotCount > 0 && (
          <span className="ml-2 text-amber-400">
            · {hotCount} hot node{hotCount !== 1 ? "s" : ""}
          </span>
        )}
      </span>

      <button
        type="button"
        onClick={onNewTask}
        className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
      >
        + New task
      </button>
    </div>
  );
}
