import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { playgroundApi } from "./api";
import type { Playground } from "@/types/playground";

export const usePlayground = (playgroundId: string | null, projectId: string) =>
  useQuery<Playground>({
    queryKey: queryKeys.playgrounds.detail(projectId, playgroundId ?? ""),
    queryFn: () => playgroundApi.getById(playgroundId!, projectId),
    enabled: !!playgroundId && !!projectId,
    retry: false,
  });

export const usePlaygroundsByOwner = (
  nodeId: string | null,
  projectId: string
) =>
  useQuery<Playground[]>({
    queryKey: queryKeys.playgrounds.byOwner(projectId, nodeId ?? ""),
    queryFn: () =>
      nodeId ? playgroundApi.getByOwnerNodeId(nodeId, projectId) : Promise.resolve([]),
    enabled: !!nodeId && !!projectId,
    retry: false,
  });
