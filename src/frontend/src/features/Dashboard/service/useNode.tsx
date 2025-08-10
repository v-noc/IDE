import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ThemeConfig } from "@/features/Dashboard/store/useThemeStore";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import API_ROUTES from "@/lib/apiRoutes";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

// Low-level API functions
const updateNodeTheme = async (
  elementKey: string,
  theme: Partial<ThemeConfig>
): Promise<ProjectTreeResponse> => {
  console.log(elementKey, " theme ", theme);
  return api<ProjectTreeResponse>(
    `${API_ROUTES.CORE}${elementKey}/update-node-theme`,
    {
      method: "POST",
      body: theme as unknown as BodyInit,
    }
  );
};

const updateNodeIcon = async (
  elementKey: string,
  icon: string
): Promise<ProjectTreeResponse> => {
  console.log(elementKey, " icon ", icon);
  return api<ProjectTreeResponse>(
    `${API_ROUTES.CORE}${elementKey}/update-icon`,
    {
      method: "POST",
      body: { icon } as unknown as BodyInit,
    }
  );
};

const updateNodeBasicInfo = async (
  elementKey: string,
  basicInfo: {
    name: string;
    description?: string;
  }
): Promise<ProjectTreeResponse> => {
  console.log(elementKey, " ", basicInfo);
  return api<ProjectTreeResponse>(
    `${API_ROUTES.CORE}${elementKey}/update-basic-info`,
    {
      method: "POST",
      body: basicInfo as unknown as BodyInit,
    }
  );
};

// Helpers to update cached project tree without refetching
function updateNodeInTree(
  root: ProjectTreeResponse,
  targetKey: string,
  updater: (node: ProjectTreeResponse) => ProjectTreeResponse
): ProjectTreeResponse {
  if (root.key === targetKey) {
    return updater(root);
  }
  if (!root.children || root.children.length === 0) return root;
  const nextChildren = root.children.map((child) =>
    updateNodeInTree(child, targetKey, updater)
  );
  // Only recreate root if children changed identities
  if (nextChildren !== root.children) {
    return { ...root, children: nextChildren };
  }
  return root;
}

// Hooks
export const useUpdateNodeTheme = (projectKey?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      elementKey,
      theme,
    }: {
      elementKey: string;
      theme: Partial<ThemeConfig>;
    }) => updateNodeTheme(elementKey, theme),
    onSuccess: async (_data, variables) => {
      if (!projectKey) return;
      queryClient.setQueryData<ProjectTreeResponse>(
        ["projectTree", projectKey],
        (old) => {
          if (!old) return old as unknown as ProjectTreeResponse;
          return updateNodeInTree(old, variables.elementKey, (node) => ({
            ...node,
            theme: { ...node.theme, ...variables.theme },
          }));
        }
      );
      // Re-assert selection to avoid any transient resets
      const { setSelectedNodeId } = useProjectStore.getState();
      setSelectedNodeId(variables.elementKey);
      // Optionally refetch in background without breaking selection
      // await queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey], refetchType: "inactive" });
    },
  });
};

export const useUpdateNodeIcon = (projectKey?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ elementKey, icon }: { elementKey: string; icon: string }) =>
      updateNodeIcon(elementKey, icon),

    onSuccess: async (_data, variables) => {
      if (!projectKey) return;
      queryClient.setQueryData<ProjectTreeResponse>(
        ["projectTree", projectKey],
        (old) => {
          if (!old) return old as unknown as ProjectTreeResponse;
          return updateNodeInTree(old, variables.elementKey, (node) => ({
            ...node,
            icon: variables.icon,
          }));
        }
      );
      const { setSelectedNodeId } = useProjectStore.getState();
      setSelectedNodeId(variables.elementKey);
    },
  });
};

export const useUpdateNodeBasicInfo = (projectKey?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      elementKey,
      basicInfo,
    }: {
      elementKey: string;
      basicInfo: { name: string; description?: string };
    }) => updateNodeBasicInfo(elementKey, basicInfo),

    onSuccess: async (_data, variables) => {
      if (!projectKey) return;
      queryClient.setQueryData<ProjectTreeResponse>(
        ["projectTree", projectKey],
        (old) => {
          if (!old) return old as unknown as ProjectTreeResponse;
          return updateNodeInTree(old, variables.elementKey, (node) => ({
            ...node,
            name: variables.basicInfo.name,
            description: variables.basicInfo.description,
          }));
        }
      );
      const { setSelectedNodeId } = useProjectStore.getState();
      setSelectedNodeId(variables.elementKey);
    },
  });
};
