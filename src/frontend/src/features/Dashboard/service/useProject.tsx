import { useMutation, useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ThemeConfig } from "../store/useThemeStore";
import getIcons from "@/features/Dashboard/utils/getIcons";

export type NodeType =
  | "folder"
  | "file"
  | "project"
  | "function"
  | "class"
  | "package"
  | "virtual_folder";
export interface ProjectTreeResponse {
  key: string;
  name: string;
  path?: string;
  node_type: NodeType;
  label?: string;
  icon?: string;
  children: ProjectTreeResponse[];
  isVirtual?: boolean;
  parentId?: string | null;
  description?: string | null;
  theme?: ThemeConfig;
}

export interface VirtualFolderResponse {
  key: string;
  name: string;
  node_type: NodeType;
  qname: string;
  description?: string | null;
  link_to?: {
    id: string;
    name: string;
    qname: string;
    node_type: NodeType;
    icon?: string;
    theme?: ThemeConfig;
  } | null;
  children: VirtualFolderResponse[];
  call_order?: number | null;
  icon?: string;
  theme?: ThemeConfig;
  imports?: Array<{
    _key: string;
    id: string;
    from_id: string;
    to_id: string;
    from_parent_virtual_folder_id?: string | null;
    to_parent_virtual_folder_id?: string | null;
    alias: string;
    qname: string;
  }> | null;
}

export interface VirtualFolderCreateRequest {
  name: string;
  description?: string;
  project_id: string;
}

export interface VirtualFolderUpdateRequest {
  name?: string;
  description?: string;
}

export interface AddCodeElementRequest {
  element_id: string;
  parent_folder_key: string;
}

export const useGetProjectTreeWithKeyProject = ({ key }: { key: string }) => {
  return useQuery({
    queryKey: ["projectTree", key],
    queryFn: () => getProjectTreeWithKey(key),
    enabled: !!key,
  });
};

export const useCreateVirtualFolder = ({
  projectKey,
  name,
  description,
}: {
  projectKey: string;
  name: string;
  description: string;
}) => {
  return useMutation({
    mutationFn: () => createVirtualFolder(projectKey, name, description),
  });
};

export const useUpdateVirtualFolder = (
  projectKey: string,
  folderKey: string
) => {
  return useMutation({
    mutationFn: (data: VirtualFolderUpdateRequest) =>
      updateVirtualFolder(projectKey, folderKey, data),
  });
};

export const useGetVirtualFolder = (projectKey: string, folderKey: string) => {
  return useQuery<VirtualFolderResponse>({
    queryKey: ["virtualFolder", projectKey, folderKey],
    queryFn: () => getVirtualFolder(projectKey, folderKey),
    enabled: !!projectKey && !!folderKey,
  });
};

export const useAddCodeElementToVirtualFolder = (
  projectKey: string,
  folderKey: string
) => {
  return useMutation({
    mutationFn: (data: AddCodeElementRequest) =>
      addCodeElementToVirtualFolder(projectKey, folderKey, data),
  });
};

export const useRemoveCodeElementFromVirtualFolder = (
  projectKey: string,
  folderKey: string
) => {
  return useMutation({
    mutationFn: (elementKey: string) =>
      removeCodeElementFromVirtualFolder(projectKey, folderKey, elementKey),
  });
};

const createVirtualFolder = async (
  projectKey: string,
  name: string,
  description?: string
): Promise<VirtualFolderResponse> => {
  const response = await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        description,
      }),
    }
  );
  return response as VirtualFolderResponse;
};

const updateVirtualFolder = async (
  projectKey: string,
  folderKey: string,
  data: VirtualFolderUpdateRequest
): Promise<VirtualFolderResponse> => {
  const response = await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}${folderKey}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );
  return response as VirtualFolderResponse;
};

const getVirtualFolder = async (
  projectKey: string,
  folderKey: string
): Promise<VirtualFolderResponse> => {
  const response = await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}${folderKey}`
  );
  return response as VirtualFolderResponse;
};

const addCodeElementToVirtualFolder = async (
  projectKey: string,
  folderKey: string,
  data: AddCodeElementRequest
): Promise<VirtualFolderResponse> => {
  const response = await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}${folderKey}/add-code-element`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );
  return response as VirtualFolderResponse;
};

const removeCodeElementFromVirtualFolder = async (
  projectKey: string,
  folderKey: string,
  elementKey: string
): Promise<void> => {
  const response = await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}${folderKey}/code-element/${elementKey}`,
    {
      method: "DELETE",
    }
  );
  return response as void;
};

const getProjectTreeWithKey = async (
  key: string
): Promise<ProjectTreeResponse> => {
  const response = await api(`${API_ROUTES.PROJECTS}${key}/tree`);
  return response as ProjectTreeResponse;
};

export const useCreatePathForElement = (
  projectKey: string,
  elementKey: string
) => {
  return useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      createPathForElement(projectKey, elementKey, data),
  });
};

const createPathForElement = async (
  projectKey: string,
  elementKey: string,
  data: { name: string; description: string }
): Promise<VirtualFolderResponse> => {
  const response = await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}create-path/${elementKey}`,
    {
      method: "POST",
      body: data as unknown as BodyInit,
    }
  );
  return response as VirtualFolderResponse;
};

function normalizeVirtualFolderThemeAndIcon(
  folder: VirtualFolderResponse
): VirtualFolderResponse {
  const icon =
    folder.icon ||
    folder.link_to?.icon ||
    (folder.link_to ? getIcons(folder.link_to.node_type) : undefined);
  const theme = folder.theme || folder.link_to?.theme;
  const children = (folder.children || []).map(
    normalizeVirtualFolderThemeAndIcon
  );
  return { ...folder, icon, theme, children };
}

export const useGetVirtualFolders = (projectKey: string) => {
  return useQuery<VirtualFolderResponse[]>({
    queryKey: ["virtualFolders", projectKey],
    queryFn: async () => {
      const response = await api(
        `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}`
      );
      const items = response as VirtualFolderResponse[];
      return items.map(normalizeVirtualFolderThemeAndIcon);
    },
    enabled: !!projectKey,
  });
};

export const useDeleteVirtualFolder = (projectKey: string) => {
  return useMutation({
    mutationFn: (folderKey: string) =>
      deleteVirtualFolder(projectKey, folderKey),
  });
};

const deleteVirtualFolder = async (
  projectKey: string,
  folderKey: string
): Promise<void> => {
  await api(
    `${API_ROUTES.PROJECT}${projectKey}${API_ROUTES.VIRTUAL_FOLDER}${folderKey}`,
    {
      method: "DELETE",
    }
  );
};
