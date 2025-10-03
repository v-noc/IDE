// import { useMutation, useQueryClient } from "@tanstack/react-query";
// import api from "@/lib/api";
// import type { ThemeConfig } from "@/types/project";
// import type { ProjectNodeTree, ContainerNodeTree } from "@/types/project";
// import API_ROUTES from "@/lib/apiRoutes";
// import useProjectStore from "@/features/Dashboard/store/useProjectStore";

// Low-level API functions
// const updateNodeTheme = async (
//   elementId: string,
//   theme: Partial<ThemeConfig>
// ): Promise<ProjectNodeTree> => {
//   console.log(elementId, " theme ", theme);
//   return api<ProjectNodeTree>(
//     `${API_ROUTES.CONTAINER}${elementId}update-theme`,
//     {
//       method: "POST",
//       body: theme as unknown as BodyInit,
//     }
//   );
// };

// const updateNodeBasicInfo = async (
//   elementId: string,
//   basicInfo: {
//     name: string;
//     description?: string;
//   }
// ): Promise<ProjectNodeTree> => {
//   console.log(elementId, " ", basicInfo);
//   return api<ProjectNodeTree>(
//     `${API_ROUTES.CONTAINER}${elementId}/update-basic-info`,
//     {
//       method: "POST",
//       body: basicInfo as unknown as BodyInit,
//     }
//   );
// };

// // Helpers to update cached project tree without refetching
// function updateNodeInTree(
//   root: ContainerNodeTree,
//   targetId: string,
//   updater: (node: ContainerNodeTree) => ContainerNodeTree
// ): ContainerNodeTree {
//   if (root.id === targetId) {
//     return updater(root);
//   }
//   if (!root.children || root.children.length == 0) return root;
//   const nextChildren = root.children.map((child) =>
//     updateNodeInTree(child, targetId, updater)
//   );
//   // Only recreate root if children changed identities
//   if (nextChildren !== root.children) {
//     return { ...root, children: nextChildren };
//   }
//   return root;
// }

// Hooks
// export const useUpdateNodeTheme = (projectKey?: string) => {
//   const queryClient = useQueryClient();
//   return useMutation({
//     mutationFn: ({
//       elementId,
//       theme,
//     }: {
//       elementId: string;
//       theme: Partial<ThemeConfig>;
//     }) => updateNodeTheme(elementId, theme),
//     onSuccess: async (_data, variables) => {
//       if (!projectKey) return;
//       queryClient.setQueryData<ProjectNodeTree>(
//         ["projectTree", projectKey],
//         (old) => {
//           if (!old) return old as unknown as ProjectNodeTree;
//           return updateNodeInTree(old, variables.elementId, (node) => ({
//             ...node,
//             theme: { ...node.theme_config, ...variables.theme },
//           }));
//         }
//       );
//       // Re-assert selection to avoid any transient resets
//       const { setSelectedNode } = useProjectStore.getState();
//       setSelectedNode({ id: variables.elementId, type: _data.node_type });
//       // Optionally refetch in background without breaking selection
//       // await queryClient.invalidateQueries({ queryKey: ["projectTree", projectKey], refetchType: "inactive" });
//     },
//   });
// };

// export const useUpdateNodeBasicInfo = (projectKey?: string) => {
//   const queryClient = useQueryClient();
//   return useMutation({
//     mutationFn: ({
//       elementId,
//       basicInfo,
//     }: {
//       elementId: string;
//       basicInfo: { name: string; description?: string };
//     }) => updateNodeBasicInfo(elementId, basicInfo),

//     onSuccess: async (_data, variables) => {
//       if (!projectKey) return;
//       queryClient.setQueryData<ProjectNodeTree>(
//         ["projectTree", projectKey],
//         (old) => {
//           if (!old) return old as unknown as ProjectNodeTree;
//           return updateNodeInTree(old, variables.elementId, (node) => ({
//             ...node,
//             name: variables.basicInfo.name,
//             description: variables.basicInfo.description || "",
//           }));
//         }
//       );
//       const { setSelectedNode } = useProjectStore.getState();
//       setSelectedNode({ id: variables.elementId, type: _data.node_type });
//     },
//   });
// };
