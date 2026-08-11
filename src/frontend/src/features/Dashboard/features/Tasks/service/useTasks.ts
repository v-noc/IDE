import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import queryKeys from "@/lib/queryKeys";
import { ApiError } from "@/lib/api";
import { toProjectApiId } from "@/lib/projectId";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { tasksApi } from "@/services/tasks";
import type { CreateTaskPayload, MoveTaskPayload, UpdateTaskPayload } from "@/services/tasks";
import type { BoardPayload, Task } from "@/types/tasks";

function taskMutationError(error: unknown) {
  if (error instanceof ApiError) {
    const detail = (error.response as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") {
      toast.error(detail);
      return;
    }
  }
  toast.error("Task update failed");
}

function useTaskQueryKey(projectId: string | undefined) {
  const apiProjectId = toProjectApiId(projectId);
  const branch = useVersioningStore((s) => s.branch);
  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);
  return [
    ...queryKeys.tasks.board(apiProjectId),
    branch ?? "main",
    checkedOutCommitId ?? "",
    compareToCommitId ?? "",
  ];
}

export function useTaskBoard(projectId: string | undefined) {
  return useQuery<BoardPayload>({
    queryKey: useTaskQueryKey(projectId),
    queryFn: () => tasksApi.getBoard(projectId!),
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

export function useAnchorSummary(projectId: string | undefined) {
  const apiProjectId = toProjectApiId(projectId);
  const branch = useVersioningStore((s) => s.branch);
  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);

  return useQuery({
    queryKey: [
      ...queryKeys.tasks.anchorSummary(apiProjectId),
      branch ?? "main",
      checkedOutCommitId ?? "",
      compareToCommitId ?? "",
    ],
    queryFn: () => tasksApi.getAnchorSummary(projectId!),
    enabled: !!projectId,
    staleTime: 30_000,
  });
}

export function useCreateTask(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: (payload: CreateTaskPayload) =>
      tasksApi.createTask(projectId!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
    onError: taskMutationError,
  });
}

export function useUpdateTask(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      taskId,
      payload,
    }: {
      taskId: string;
      payload: UpdateTaskPayload;
    }) => tasksApi.updateTask(projectId!, taskId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
    onError: taskMutationError,
  });
}

export function useMoveTask(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      taskId,
      payload,
    }: {
      taskId: string;
      payload: MoveTaskPayload;
    }) => tasksApi.moveTask(projectId!, taskId, payload),
    onMutate: async ({ taskId, payload }) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<BoardPayload>(queryKey);
      if (previous) {
        queryClient.setQueryData<BoardPayload>(queryKey, {
          ...previous,
          tasks: previous.tasks.map((t) =>
            t.id === taskId
              ? { ...t, status: payload.status, rank: payload.rank }
              : t,
          ),
        });
      }
      return { previous };
    },
    onError: (err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      taskMutationError(err);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
  });
}

export function useAddSubtask(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      parentId,
      payload,
    }: {
      parentId: string;
      payload: { child_id?: string; title?: string; anchors?: { node_id: string }[] };
    }) => tasksApi.addSubtask(projectId!, parentId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
    onError: taskMutationError,
  });
}

export function useRemoveSubtask(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      parentId,
      childId,
    }: {
      parentId: string;
      childId: string;
    }) => tasksApi.removeSubtask(projectId!, parentId, childId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
    onError: taskMutationError,
  });
}

export function useAddAnchor(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      taskId,
      nodeId,
    }: {
      taskId: string;
      nodeId: string;
    }) => tasksApi.addAnchor(projectId!, taskId, nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
    onError: taskMutationError,
  });
}

export function useRemoveAnchor(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      taskId,
      nodeId,
    }: {
      taskId: string;
      nodeId: string;
    }) => tasksApi.removeAnchor(projectId!, taskId, nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
    onError: taskMutationError,
  });
}

export function useAddNote(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({ taskId, text }: { taskId: string; text: string }) =>
      tasksApi.addNote(projectId!, taskId, text),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
    onError: taskMutationError,
  });
}

export function useMoveAnchor(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      taskId,
      fromNodeId,
      toNodeId,
    }: {
      taskId: string;
      fromNodeId: string;
      toNodeId: string;
    }) => tasksApi.moveAnchor(projectId!, taskId, fromNodeId, toNodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
    onError: taskMutationError,
  });
}

export function useSuggestDependencies(
  projectId: string | undefined,
  nodeId: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: [...queryKeys.tasks.suggestDeps(projectId ?? "", nodeId ?? ""), enabled],
    queryFn: () => tasksApi.suggestDependencies(projectId!, nodeId!),
    enabled: !!projectId && !!nodeId && enabled,
    staleTime: 60_000,
  });
}

export function findTaskInBoard(
  board: BoardPayload | undefined,
  taskId: string | null,
): Task | undefined {
  if (!board || !taskId) return undefined;
  return board.tasks.find((t) => t.id === taskId);
}
