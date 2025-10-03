import api from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ProjectNodeTree } from "@/types/project";
import { useQuery } from "@tanstack/react-query";

// import getIcons from "@/features/Dashboard/utils/getIcons";

export interface AddCodeElementRequest {
  element_id: string;
  parent_folder_key: string;
}

const getProjectTreeWithKey = async (key: string): Promise<ProjectNodeTree> => {
  const response = await api(`${API_ROUTES.PROJECTS}${key}`);
  return response as ProjectNodeTree;
};
export const useGetProjectTreeWithKeyProject = ({ key }: { key: string }) => {
  return useQuery({
    queryKey: ["projectTree", key],
    queryFn: () => getProjectTreeWithKey(key),
    enabled: !!key,
  });
};

// export const useCreateVirtualFolder = ({
//   projectKey,
//   name,
//   description,
// }: {
//   projectKey: string;
//   name: string;
//   description: string;
// }) => {
//   return useMutation({
//     mutationFn: () => createVirtualFolder(projectKey, name, description),
//   });
// };

// export const useUpdateVirtualFolder = (
//   projectKey: string,
//   folderKey: string
// ) => {
//   return useMutation({
//     mutationFn: (data: VirtualFolderUpdateRequest) =>
//       updateVirtualFolder(projectKey, folderKey, data),
//   });
// };

// export const useGetVirtualFolder = (projectKey: string, folderKey: string) => {
//   return useQuery<VirtualFolderResponse>({
//     queryKey: ["virtualFolder", projectKey, folderKey],
//     queryFn: () => getVirtualFolder(projectKey, folderKey),
//     enabled: !!projectKey && !!folderKey,
//   });
// };

// export const useAddCodeElementToVirtualFolder = (
//   projectKey: string,
//   folderKey: string
// ) => {
//   return useMutation({
//     mutationFn: (data: AddCodeElementRequest) =>
//       addCodeElementToVirtualFolder(projectKey, folderKey, data),
//   });
// };

// export const useRemoveCodeElementFromVirtualFolder = (
//   projectKey: string,
//   folderKey: string
// ) => {
//   return useMutation({
//     mutationFn: (elementKey: string) =>
//       removeCodeElementFromVirtualFolder(projectKey, folderKey, elementKey),
//   });
// };

// const createVirtualFolder = async (
//   projectKey: string,
//   name: string,
//   description?: string
// ): Promise<VirtualFolderResponse> => {
//   let parsedProjectKey = projectKey;
//   if (projectKey.includes("/")) {
//     parsedProjectKey = projectKey.split("/")[1];
//   }
//   const response = await api(
//     `${API_ROUTES.PROJECT}${parsedProjectKey}${API_ROUTES.VIRTUAL_FOLDER}`,
//     {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify({
//         name,
//         description,
//       }),
//     }
//   );
//   return response as VirtualFolderResponse;
// };

// const updateVirtualFolder = async (
//   projectKey: string,
//   folderKey: string,
//   data: VirtualFolderUpdateRequest
// ): Promise<VirtualFolderResponse> => {
//   let parsedFolderKey = folderKey;
//   if (folderKey.includes("/")) {
//     parsedFolderKey = folderKey.split("/")[1];
//   }
//   let parsedProjectKey = projectKey;
//   if (projectKey.includes("/")) {
//     parsedProjectKey = projectKey.split("/")[1];
//   }
//   // TODO: This is a temporary fix to handle the case where the folder key is a path

//   const response = await api(
//     `${API_ROUTES.PROJECT}${parsedProjectKey}${API_ROUTES.VIRTUAL_FOLDER}${parsedFolderKey}`,
//     {
//       method: "PUT",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(data),
//     }
//   );
//   return response as VirtualFolderResponse;
// };

// const getVirtualFolder = async (
//   projectKey: string,
//   folderKey: string
// ): Promise<VirtualFolderResponse> => {
//   let parsedProjectKey = projectKey;
//   if (projectKey.includes("/")) {
//     parsedProjectKey = projectKey.split("/")[1];
//   }
//   let parsedFolderKey = folderKey;
//   if (folderKey.includes("/")) {
//     parsedFolderKey = folderKey.split("/")[1];
//   }
//   const response = await api(
//     `${API_ROUTES.PROJECT}${parsedProjectKey}${API_ROUTES.VIRTUAL_FOLDER}${parsedFolderKey}`
//   );
//   return response as VirtualFolderResponse;
// };

// const addCodeElementToVirtualFolder = async (
//   projectKey: string,
//   folderKey: string,
//   data: AddCodeElementRequest
// ): Promise<VirtualFolderResponse> => {
//   let parsedProjectKey = projectKey;
//   if (projectKey.includes("/")) {
//     parsedProjectKey = projectKey.split("/")[1];
//   }
//   let parsedFolderKey = folderKey;
//   if (folderKey.includes("/")) {
//     parsedFolderKey = folderKey.split("/")[1];
//   }
//   const response = await api(
//     `${API_ROUTES.PROJECT}${parsedProjectKey}${API_ROUTES.VIRTUAL_FOLDER}${parsedFolderKey}/add-code-element`,
//     {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(data),
//     }
//   );
//   return response as VirtualFolderResponse;
// };

// const removeCodeElementFromVirtualFolder = async (
//   projectKey: string,
//   folderKey: string,
//   elementKey: string
// ): Promise<void> => {
//   let parsedFolderKey = folderKey;
//   if (folderKey.includes("/")) {
//     parsedFolderKey = folderKey.split("/")[1];
//   }
//   // TODO: This is a temporary fix to handle the case where the folder key is a path
//   let parsedElementKey = elementKey;
//   if (elementKey.includes("/")) {
//     parsedElementKey = elementKey.split("/")[1];
//   }
//   const response = await api(
//     `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}${parsedFolderKey}/code-element/${parsedElementKey}`,
//     {
//       method: "DELETE",
//     }
//   );
//   return response as void;
// };

// export const useCreatePathForElement = (
//   projectKey: string,
//   elementKey: string
// ) => {
//   return useMutation({
//     mutationFn: (data: { name: string; description: string }) =>
//       createPathForElement(projectKey, elementKey, data),
//   });
// };

// const createPathForElement = async (
//   projectKey: string,
//   elementKey: string,
//   data: { name: string; description: string }
// ): Promise<VirtualFolderResponse> => {
//   let parsedProjectKey = projectKey;
//   if (projectKey.includes("/")) {
//     parsedProjectKey = projectKey.split("/")[1];
//   }
//   const response = await api(
//     `${API_ROUTES.PROJECT}${parsedProjectKey}${API_ROUTES.VIRTUAL_FOLDER}create-path/${elementKey}`,
//     {
//       method: "POST",
//       body: data as unknown as BodyInit,
//     }
//   );
//   return response as VirtualFolderResponse;
// };

// function normalizeVirtualFolderThemeAndIcon(
//   folder: VirtualFolderResponse
// ): VirtualFolderResponse {
//   const icon =
//     folder.icon ||
//     folder.link_to?.icon ||
//     (folder.link_to ? getIcons(folder.link_to.node_type) : undefined);
//   const theme = folder.theme || folder.link_to?.theme;
//   const children = (folder.children || []).map(
//     normalizeVirtualFolderThemeAndIcon
//   );
//   return { ...folder, icon, theme, children };
// }

// export const useGetVirtualFolders = (projectKey: string) => {
//   return useQuery<VirtualFolderResponse[]>({
//     queryKey: ["virtualFolders", projectKey],
//     queryFn: async () => {
//       const response = await api(
//         `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}`
//       );
//       const items = response as VirtualFolderResponse[];
//       return items.map(normalizeVirtualFolderThemeAndIcon);
//     },
//     enabled: !!projectKey,
//   });
// };

// export const useDeleteVirtualFolder = (projectKey: string) => {
//   return useMutation({
//     mutationFn: (folderKey: string) =>
//       deleteVirtualFolder(projectKey, folderKey),
//   });
// };

// const deleteVirtualFolder = async (
//   projectKey: string,
//   folderKey: string
// ): Promise<void> => {
//   let parsedProjectKey = projectKey;
//   if (projectKey.includes("/")) {
//     parsedProjectKey = projectKey.split("/")[1];
//   }
//   // TODO: This is a temporary fix to handle the case where the folder key is a path
//   let parsedFolderKey = folderKey;
//   if (folderKey.includes("/")) {
//     parsedFolderKey = folderKey.split("/")[1];
//   }
//   await api(
//     `${API_ROUTES.PROJECT}${parsedProjectKey}${API_ROUTES.VIRTUAL_FOLDER}${parsedFolderKey}`,
//     {
//       method: "DELETE",
//     }
//   );
// };
