import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { toProjectApiId } from "@/lib/projectId";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { tasksApi } from "@/services/tasks";
import type { CreateTaskPayload, MoveTaskPayload, UpdateTaskPayload } from "@/services/tasks";
import type { BoardPayload, Task } from "@/types/tasks";

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
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
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
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });
}

export function useAddNote(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({ taskId, text }: { taskId: string; text: string }) =>
      tasksApi.addNote(projectId!, taskId, text),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });
}

export function useReAnchor(projectId: string | undefined) {
  const queryClient = useQueryClient();
  const queryKey = useTaskQueryKey(projectId);

  return useMutation({
    mutationFn: ({
      taskId,
      index,
      nodeId,
    }: {
      taskId: string;
      index: number;
      nodeId: string;
    }) => tasksApi.reAnchor(projectId!, taskId, index, nodeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.anchorSummary(toProjectApiId(projectId)),
      });
    },
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
