import { useMutation, useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
export interface ProjectTreeResponse {
  key: string;
  name: string;
  path?: string;
  node_type: string;
  label?: string;
  children: ProjectTreeResponse[];
  isVirtual?: boolean;
  parentId?: string | null;
  description?: string | null;
}

export interface VirtualFolderResponse {
  key: string;
  name: string;
  node_type: string;
  qname: string;
  description?: string | null;
  link_to?: {
    id: string;
    name: string;
    qname: string;
    node_type: string;
  } | null;
  children: VirtualFolderResponse[];
  call_order?: number | null;
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
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder`,
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
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder/${folderKey}`,
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
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder/${folderKey}`
  );
  return response as VirtualFolderResponse;
};

const addCodeElementToVirtualFolder = async (
  projectKey: string,
  folderKey: string,
  data: AddCodeElementRequest
): Promise<VirtualFolderResponse> => {
  const response = await api(
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder/${folderKey}/add-code-element`,
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
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder/${folderKey}/code-element/${elementKey}`,
    {
      method: "DELETE",
    }
  );
  return response as void;
};

const getProjectTreeWithKey = async (
  key: string
): Promise<ProjectTreeResponse> => {
  const response = await api(`${API_ROUTES.PROJECT}${key}/tree`);
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
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder/create-path/${elementKey}`,
    {
      method: "POST",
      body: data as unknown as BodyInit,
    }
  );
  return response as VirtualFolderResponse;
};

export const useGetVirtualFolders = (projectKey: string) => {
  return useQuery<VirtualFolderResponse[]>({
    queryKey: ["virtualFolders", projectKey],
    queryFn: async () => {
      const response = await api(
        `${API_ROUTES.PROJECT}${projectKey}/virtual-folders`
      );
      return response as VirtualFolderResponse[];
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
    `${API_ROUTES.VIRTUAL_FOLDER}${projectKey}/virtual-folder/${folderKey}`,
    {
      method: "DELETE",
    }
  );
};
