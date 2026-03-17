import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { playgroundApi } from "./api";
import type {
  CreatePlaygroundPayload,
  RunPlaygroundCodePayload,
  UpdatePlaygroundPayload,
} from "@/types/playground";

function invalidatePlaygroundQueries(
  queryClient: ReturnType<typeof useQueryClient>
) {
  queryClient.invalidateQueries({ queryKey: queryKeys.playgrounds.all });
}

export const useCreatePlayground = (projectId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreatePlaygroundPayload) =>
      playgroundApi.create(payload, projectId),
    onSuccess: () => {
      invalidatePlaygroundQueries(queryClient);
    },
  });
};

export const useUpdatePlayground = (projectId: string, playgroundId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdatePlaygroundPayload) =>
      playgroundApi.update(playgroundId, payload, projectId),
    onSuccess: () => {
      invalidatePlaygroundQueries(queryClient);
    },
  });
};

export const useDeletePlayground = (projectId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (playgroundId: string) => playgroundApi.delete(playgroundId, projectId),
    onSuccess: () => {
      invalidatePlaygroundQueries(queryClient);
    },
  });
};

export const useRunPlaygroundCode = (projectId: string) =>
  useMutation({
    mutationFn: (payload: RunPlaygroundCodePayload) =>
      playgroundApi.runCode(payload, projectId),
  });
