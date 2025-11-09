import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface DocumentType {
  _id: string; // backend returns _id; service maps to this property
  _key: string;
  name: string;
  description: string;
  data: string;
  created_at: string;
  updated_at: string;
}

export interface CreateDocumentRequest {
  name: string;
  description: string;
  node_id: string; // parent node id or key
}

export interface UpdateDocumentRequest {
  id: string; // document id or key (can be full _id or _key)
  name?: string;
  description?: string;
  data?: string;
}

// Backend shape we receive from API
interface BackendDocumentRaw {
  _id?: string;
  id?: string;
  _key?: string;
  key?: string;
  name: string;
  description: string;
  data: string;
  created_at: string;
  updated_at: string;
}

const getKeyFromId = (id: string): string =>
  id.includes("/") ? id.split("/").pop() as string : id;

const getDocuments = async (nodeId: string): Promise<DocumentType[]> => {
  const response = await api(`${API_ROUTES.DOCUMENTS}${nodeId}`);
  const list = response as unknown as BackendDocumentRaw[];
  // Map backend _id -> id for convenience
  return list.map((d) => ({
    _id: d._id ?? d.id!,
    _key: d._key ?? d.key!,
    name: d.name,
    description: d.description,
    data: d.data,
    created_at: d.created_at,
    updated_at: d.updated_at,
  }));
};

const createDocument = async (
  payload: CreateDocumentRequest,
): Promise<DocumentType> => {
  const response = await api(`${API_ROUTES.DOCUMENTS}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const d = response as unknown as BackendDocumentRaw;
  return {
    _id: d._id ?? d.id!,
    _key: d._key ?? d.key!,
    name: d.name,
    description: d.description,
    data: d.data,
    created_at: d.created_at,
    updated_at: d.updated_at,
  };
};


const updateDocument = async (
  payload: UpdateDocumentRequest,
): Promise<DocumentType> => {
  const key = getKeyFromId(payload.id);
  const body = {
    name: payload.name,
    description: payload.description,
    data: payload.data,
  } as Partial<Omit<UpdateDocumentRequest, "id">>;
  const response = await api(`${API_ROUTES.DOCUMENTS}${key}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
  const d = response as unknown as BackendDocumentRaw;
  return {
    _id: d._id ?? d.id!,
    _key: d._key ?? d.key!,
    name: d.name,
    description: d.description,
    data: d.data,
    created_at: d.created_at,
    updated_at: d.updated_at,
  };
};

const deleteDocument = async (
  documentId: string,
  nodeId: string,
): Promise<void> => {
  const key = getKeyFromId(documentId);
  await api(`${API_ROUTES.DOCUMENTS}${key}?node_id=${encodeURIComponent(nodeId)}`, {
    method: "DELETE",
  });
};

export const useGetDocuments = (nodeId: string) => {

  return useQuery<DocumentType[]>({
    queryKey: ["documents", nodeId],
    queryFn: () => getDocuments(nodeId),
  });
};

export const useCreateDocument = () => {
  return useMutation<DocumentType, Error, CreateDocumentRequest>({
    mutationFn: (payload) => createDocument(payload),
  });
};

export const useUpdateDocument = (nodeId: string) => {

  return useMutation<DocumentType, Error, UpdateDocumentRequest>({
    mutationFn: (payload) => updateDocument(payload),
    onSuccess: (data) => {
      console.log("notify document updated ", data, " ", nodeId);

    },
  });
};

export const useDeleteDocument = () => {
  return useMutation<void, Error, { documentId: string; nodeId: string }>({
    mutationFn: ({ documentId, nodeId }) => deleteDocument(documentId, nodeId),
  });
};

