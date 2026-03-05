import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { GroupApiItemType, GroupApiType } from "./groupApiUtils";

type CreateGroupRequest = {
  name: string;
  description: string;
  children: Array<{ id: string; type: GroupApiItemType }>;
};

type GroupApiContext = {
  projectId: string;
  groupType: GroupApiType;
  branchName?: string;
};

const withGroupQuery = (
  basePath: string,
  { projectId, groupType }: GroupApiContext,
  extra: Record<string, string | undefined> = {},
) => {
  const params = new URLSearchParams({
    project_id: projectId,
    group_type: groupType,
  });

  Object.entries(extra).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });

  return `${basePath}?${params.toString()}`;
};

const withOptionalBranch = (branchName?: string) =>
  branchName ? { "X-Vnoc-Branch": branchName } : undefined;

const createGroup = async (
  createGroupPayload: CreateGroupRequest,
  context: GroupApiContext,
  parentNodeId?: string,
) => {
  return api(
    withGroupQuery(API_ROUTES.GROUPS, context, {
      parent_node_id: parentNodeId,
    }),
    {
      method: "POST",
      body: createGroupPayload,
      headers: withOptionalBranch(context.branchName),
    },
  );
};

export const useCreateGroup = ({
  parentNodeId,
  projectKey,
  projectId,
  groupType,
  branchName,
}: {
  parentNodeId: string;
  projectKey: string;
  projectId: string;
  groupType: GroupApiType;
  branchName?: string;
}) => {
  const queryClient = useQueryClient();
  let newParentId = undefined;
  if (parentNodeId && parentNodeId.startsWith("Project") == false) {
    newParentId = parentNodeId;
  }
  return useMutation({
    mutationFn: (createGroupPayload: CreateGroupRequest) =>
      createGroup(
        createGroupPayload,
        {
          projectId,
          groupType,
          branchName,
        },
        newParentId,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey] });
    },
  });
};

const updateGroup = async (
  groupId: string,
  updateData: { name?: string; description?: string },
  context: GroupApiContext,
) => {
  return api(
    withGroupQuery(API_ROUTES.GROUPS, context, { group_id: groupId }),
    {
      method: "PATCH",
      body: updateData,
      headers: withOptionalBranch(context.branchName),
    },
  );
};

export const useUpdateGroup = ({
  groupId,
  projectKey,
  projectId,
  groupType,
  branchName,
}: {
  groupId: string;
  projectKey: string;
  projectId: string;
  groupType: GroupApiType;
  branchName?: string;
}) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (updateData: { name?: string; description?: string }) =>
      updateGroup(groupId, updateData, {
        projectId,
        groupType,
        branchName,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey] });
    },
  });
};

const addChildToGroup = async (
  groupId: string,
  childId: string,
  itemType: GroupApiItemType,
  context: GroupApiContext,
) => {
  return api(
    withGroupQuery(`${API_ROUTES.GROUPS}children`, context, {
      group_id: groupId,
      child_id: childId,
    }),
    {
      method: "POST",
      body: { item_type: itemType },
      headers: withOptionalBranch(context.branchName),
    },
  );
};

const removeChildFromGroup = async (
  groupId: string,
  childId: string,
  itemType: GroupApiItemType,
  newParentId: string,
  context: GroupApiContext,
) => {
  return api(
    withGroupQuery(`${API_ROUTES.GROUPS}children`, context, {
      group_id: groupId,
      child_id: childId,
      item_type: itemType,
      new_parent_id: newParentId,
    }),
    {
      method: "DELETE",
      headers: withOptionalBranch(context.branchName),
    },
  );
};

export const useGroupUpdate = ({
  groupId,
  projectKey,
  projectId,
  groupType,
  newParentId,
  branchName,
}: {
  groupId: string;
  projectKey: string;
  projectId: string;
  groupType: GroupApiType;
  newParentId: string;
  branchName?: string;
}) => {
  const queryClient = useQueryClient();
  const addChildToGroupMutation = useMutation({
    mutationFn: ({
      childId,
      itemType,
    }: {
      childId: string;
      itemType: GroupApiItemType;
    }) =>
      addChildToGroup(groupId, childId, itemType, {
        projectId,
        groupType,
        branchName,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey] });
    },
  });

  const removeChildFromGroupMutation = useMutation({
    mutationFn: ({
      childId,
      itemType,
    }: {
      childId: string;
      itemType: GroupApiItemType;
    }) =>
      removeChildFromGroup(groupId, childId, itemType, newParentId, {
        projectId,
        groupType,
        branchName,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey] });
    },
  });

  return {
    addChildToGroupMutation,
    removeChildFromGroupMutation,
  };
};

const deleteGroup = async (groupId: string, context: GroupApiContext) => {
  return api(
    withGroupQuery(API_ROUTES.GROUPS, context, { group_id: groupId }),
    {
      method: "DELETE",
      headers: withOptionalBranch(context.branchName),
    },
  );
};

export const useDeleteGroup = ({
  groupId,
  projectKey,
  projectId,
  groupType,
  branchName,
}: {
  groupId: string;
  projectKey: string;
  projectId: string;
  groupType: GroupApiType;
  branchName?: string;
}) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      deleteGroup(groupId, {
        projectId,
        groupType,
        branchName,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey] });
    },
  });
};
