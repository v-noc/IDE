import { queryOptions } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { agentApi } from "./api";

export const agentConversationSummariesQueryOptions = (limit = 50) =>
  queryOptions({
    queryKey: queryKeys.agent.conversations.list(limit),
    queryFn: () => agentApi.listConversations(limit),
    staleTime: 30_000,
  });

export const agentConversationHydrationQueryOptions = (
  conversationId: string | null,
  messageLimit = 200,
) =>
  queryOptions({
    queryKey: queryKeys.agent.conversations.detail(conversationId ?? ""),
    queryFn: () => agentApi.hydrateConversation(conversationId!, messageLimit),
    enabled: Boolean(conversationId),
    staleTime: 10_000,
  });
