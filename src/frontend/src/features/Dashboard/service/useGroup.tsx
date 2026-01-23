import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import { useMutation, useQueryClient } from "@tanstack/react-query";

type CreateGroupRequest = {
  name: string;
  description: string;
  children_ids: string[];
};

const createGroup = async (
  parent_node_id: string,
  create_group: CreateGroupRequest
) => {
  return api(`${API_ROUTES.GROUPS}${parent_node_id}`, {
    method: "POST",
    body: create_group,
  });
};

export const useCreateGroup = (parent_node_id: string, project_key: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (create_group: CreateGroupRequest) =>
      createGroup(parent_node_id, create_group),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });
};

const updateGroup = async (
  group_id: string,
  update_data: { name?: string; description?: string }
) => {
  return api(`${API_ROUTES.GROUPS}${group_id}`, {
    method: "PATCH",
    body: update_data,
  });
};

export const useUpdateGroup = (group_id: string, project_key: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (update_data: { name?: string; description?: string }) =>
      updateGroup(group_id, update_data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });
};

const addChildToGroup = async (group_id: string, child_id: string) => {
  return api(`${API_ROUTES.GROUPS}${group_id}/children`, {
    method: "POST",
    body: { child_id },
  });
};

const removeChildFromGroup = async (group_id: string, child_id: string) => {
  return api(`${API_ROUTES.GROUPS}${group_id}/children/${child_id}`, {
    method: "DELETE",
  });
};

export const useGroupUpdate = (group_id: string, project_key: string) => {
  const queryClient = useQueryClient();
  const addChildToGroupMutation = useMutation({
    mutationFn: (child_id: string) => addChildToGroup(group_id, child_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });

  const removeChildFromGroupMutation = useMutation({
    mutationFn: (child_id: string) => removeChildFromGroup(group_id, child_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });

  return {
    addChildToGroupMutation,
    removeChildFromGroupMutation,
  };
};

const deleteGroup = async (group_id: string) => {
  return api(`${API_ROUTES.GROUPS}${group_id}`, {
    method: "DELETE",
  });
};

export const useDeleteGroup = (group_id: string, project_key: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deleteGroup(group_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });
};
