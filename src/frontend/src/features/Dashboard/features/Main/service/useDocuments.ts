import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();

  return useMutation<DocumentType, Error, UpdateDocumentRequest>({
    mutationFn: (payload) => updateDocument(payload),
    onSuccess: (updatedDocument, variables) => {
      // Update the cache directly without invalidating/refetching
      // This prevents cursor glitches and keeps UI in sync between main view and right sidebar
      queryClient.setQueryData<DocumentType[]>(
        ["documents", nodeId],
        (oldData) => {
          if (!oldData) return oldData;

          let hasChanges = false;
          const updatedDocs = oldData.map((doc) => {
            if (doc._key !== updatedDocument._key) {
              return doc; // Return same reference for unchanged docs
            }

            // Use updated_at timestamp to determine if document was actually updated
            // Only update if server's updated_at is newer than cache's updated_at
            const serverUpdatedAt = new Date(updatedDocument.updated_at).getTime();
            const cacheUpdatedAt = new Date(doc.updated_at).getTime();

            // If server timestamp is not newer, don't update (prevents unnecessary re-renders)
            if (serverUpdatedAt <= cacheUpdatedAt) {
              return doc; // Return same reference - prevents unnecessary re-renders
            }

            hasChanges = true;
            return {
              ...doc,
              // Update fields from server response (source of truth)
              // Only update fields that were provided in the mutation
              ...(variables.data !== undefined && { data: updatedDocument.data }),
              ...(variables.name !== undefined && { name: updatedDocument.name }),
              ...(variables.description !== undefined && {
                description: updatedDocument.description,
              }),
              // Always update timestamp from server response
              updated_at: updatedDocument.updated_at,
            };
          });

          // Return same array reference if nothing changed
          return hasChanges ? updatedDocs : oldData;
        }
      );
    },
  });
};

export const useDeleteDocument = () => {
  return useMutation<void, Error, { documentId: string; nodeId: string }>({
    mutationFn: ({ documentId, nodeId }) => deleteDocument(documentId, nodeId),
  });
};

