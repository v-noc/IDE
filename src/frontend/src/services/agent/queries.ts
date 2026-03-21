import { queryOptions } from "@tanstack/react-query";
import { isAgentPreviewConversationId } from "@/features/Dashboard/features/Agent/constants/agentPreviewConversation";
import queryKeys from "@/lib/queryKeys";
import { agentApi } from "./api";

export const agentConversationSummariesQueryOptions = (
  projectId: string,
  branch: string | null | undefined,
  ref: string | null | undefined,
  compareTo: string | null | undefined,
  limit = 50,
) =>
  queryOptions({
    queryKey: queryKeys.agent.conversations.list(
      projectId,
      limit,
      branch,
      ref,
      compareTo,
    ),
    queryFn: () => agentApi.listConversations(projectId, limit),
    enabled: Boolean(projectId),
    staleTime: 30_000,
  });

export const agentConversationHydrationQueryOptions = (
  projectId: string,
  conversationId: string | null,
  branch: string | null | undefined,
  ref: string | null | undefined,
  compareTo: string | null | undefined,
  messageLimit = 200,
) =>
  queryOptions({
    queryKey: queryKeys.agent.conversations.detail(
      projectId,
      conversationId ?? "",
      branch,
      ref,
      compareTo,
    ),
    queryFn: () =>
      agentApi.hydrateConversation(projectId, conversationId!, messageLimit),
    enabled: Boolean(
      projectId && conversationId && !isAgentPreviewConversationId(conversationId),
    ),
    staleTime: 10_000,
  });
