import type { StateCreator } from "zustand";
import type { ProjectStore } from "../useProjectStore";
import type { TaskFilters, TaskType, TaskPriority, TaskView } from "@/types/tasks";

export interface TasksSlice {
  selectedTaskId: string | null;
  lensTaskId: Record<string, string | null>;
  taskFilters: TaskFilters;
  taskView: Record<string, TaskView>;
  listCollapsed: Record<string, string[]>;
  listScrollToBacklog: Record<string, boolean>;
  newTaskModalOpen: boolean;
  newTaskPreset: {
    columnId?: string;
    anchorNodeId?: string;
    anchorQname?: string;
    anchorKind?: string;
  } | null;
  setSelectedTaskId: (taskId: string | null) => void;
  setLensTaskId: (tabId: string, taskId: string | null) => void;
  setTaskFilters: (filters: Partial<TaskFilters>) => void;
  setTaskView: (tabId: string, view: TaskView) => void;
  toggleListGroup: (tabId: string, groupId: string) => void;
  requestListBacklogScroll: (tabId: string) => void;
  clearListBacklogScroll: (tabId: string) => void;
  openNewTaskModal: (preset?: TasksSlice["newTaskPreset"]) => void;
  closeNewTaskModal: () => void;
}

const defaultFilters: TaskFilters = {
  query: "",
  type: "all",
  label: "",
  priority: "all",
};

/** Stable default — never inline `?? ["done"]` in selectors (new ref every run → render loop). */
export const DEFAULT_LIST_COLLAPSED: readonly string[] = ["done"];

export const createTasksSlice: StateCreator<
  ProjectStore,
  [["zustand/immer", never], ["zustand/devtools", never]],
  [],
  TasksSlice
> = (set) => ({
  selectedTaskId: null,
  lensTaskId: {},
  taskFilters: { ...defaultFilters },
  taskView: {},
  listCollapsed: {},
  listScrollToBacklog: {},
  newTaskModalOpen: false,
  newTaskPreset: null,

  setSelectedTaskId: (taskId) =>
    set((state) => {
      state.selectedTaskId = taskId;
    }),

  setLensTaskId: (tabId, taskId) =>
    set((state) => {
      state.lensTaskId[tabId] = taskId;
    }),

  setTaskFilters: (filters) =>
    set((state) => {
      state.taskFilters = { ...state.taskFilters, ...filters };
    }),

  setTaskView: (tabId, view) =>
    set((state) => {
      state.taskView[tabId] = view;
    }),

  toggleListGroup: (tabId, groupId) =>
    set((state) => {
      const current = state.listCollapsed[tabId] ?? DEFAULT_LIST_COLLAPSED;
      const next = current.includes(groupId)
        ? current.filter((id) => id !== groupId)
        : [...current, groupId];
      state.listCollapsed[tabId] = next;
    }),

  requestListBacklogScroll: (tabId) =>
    set((state) => {
      state.listScrollToBacklog[tabId] = true;
    }),

  clearListBacklogScroll: (tabId) =>
    set((state) => {
      state.listScrollToBacklog[tabId] = false;
    }),

  openNewTaskModal: (preset) =>
    set((state) => {
      state.newTaskModalOpen = true;
      state.newTaskPreset = preset ?? null;
    }),

  closeNewTaskModal: () =>
    set((state) => {
      state.newTaskModalOpen = false;
      state.newTaskPreset = null;
    }),
});

export type { TaskType, TaskPriority, TaskView };
