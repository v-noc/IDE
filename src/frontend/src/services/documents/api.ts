import { api } from "@/lib/api";
import API_ROUTES from '@/lib/apiRoutes';

export interface DocumentData {
  id: string;
  name: string;
  description: string;
  data: string;
  created_at: string;
  updated_at: string;
}

export interface CreateDocumentRequest {
  name: string;
  description: string;
  node_id: string;
}

export interface UpdateDocumentRequest {
  id: string;
  name?: string;
  description?: string;
  data?: string;
}

// Backend shape we receive from API
interface BackendDocumentRaw {
  id?: string;
  name: string;
  description: string;
  data: string;
  created_at: string;
  updated_at: string;
}

const mapBackendDocument = (d: BackendDocumentRaw): DocumentData => ({
  id: d.id ?? "",
  name: d.name,
  description: d.description,
  data: d.data,
  created_at: d.created_at,
  updated_at: d.updated_at,
});

export const documentsApi = {
  getDocuments: async (nodeId: string): Promise<DocumentData[]> => {
    const response = await api(`${API_ROUTES.DOCUMENTS}${nodeId}`);
    const list = response as unknown as BackendDocumentRaw[];
    return list.map(mapBackendDocument);
  },

  createDocument: async (payload: CreateDocumentRequest): Promise<DocumentData> => {
    const response = await api(`${API_ROUTES.DOCUMENTS}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const d = response as unknown as BackendDocumentRaw;
    return mapBackendDocument(d);
  },

  updateDocument: async (payload: UpdateDocumentRequest): Promise<DocumentData> => {
    const key = getKeyFromId(payload.id);
    const body = {
      name: payload.name,
      description: payload.description,
      data: payload.data,
    } as Partial<Omit<UpdateDocumentRequest, "id">>;
    const response = await api(`${API_ROUTES.DOCUMENTS}${payload.id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
    const d = response as unknown as BackendDocumentRaw;
    return mapBackendDocument(d);
  },

  deleteDocument: async (documentId: string, nodeId: string): Promise<void> => {
    const key = getKeyFromId(documentId);
    await api(`${API_ROUTES.DOCUMENTS}${key}?node_id=${encodeURIComponent(nodeId)}`, {
      method: "DELETE",
    });
  },
};

