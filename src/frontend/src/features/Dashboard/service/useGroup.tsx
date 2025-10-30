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
  return api(`${API_ROUTES.GROUPS}${parent_node_id}/create-group`, {
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
