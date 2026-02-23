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
  node_id: string;
  name?: string;
  description?: string;
  data?: string;
}

function buildQueryString(params: Record<string, string>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== '') search.set(k, v);
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
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
  getDocuments: async (nodeId: string, projectId: string): Promise<DocumentData[]> => {
    const qs = buildQueryString({ node_id: nodeId, project_id: projectId });
    const response = await api(`${API_ROUTES.DOCUMENTS}${qs}`);
    const list = response as unknown as BackendDocumentRaw[];
    return list.map(mapBackendDocument);
  },

  createDocument: async (payload: CreateDocumentRequest, projectId: string): Promise<DocumentData> => {
    const qs = buildQueryString({ project_id: projectId });
    const response = await api(`${API_ROUTES.DOCUMENTS}${qs}`, {
      method: "POST",
      body: payload,
    });
    const d = response as unknown as BackendDocumentRaw;
    return mapBackendDocument(d);
  },

  updateDocument: async (payload: UpdateDocumentRequest, projectId: string): Promise<DocumentData> => {
    const body = {
      node_id: payload.node_id,
      name: payload.name,
      description: payload.description,
      data: payload.data,
    };
    const qs = buildQueryString({ document_id: payload.id, project_id: projectId });
    const response = await api(`${API_ROUTES.DOCUMENTS}${qs}`, {
      method: "PUT",
      body,
    });
    const d = response as unknown as BackendDocumentRaw;
    return mapBackendDocument(d);
  },

  deleteDocument: async (documentId: string, nodeId: string, projectId: string): Promise<void> => {
    const qs = buildQueryString({ document_id: documentId, node_id: nodeId, project_id: projectId });
    await api(`${API_ROUTES.DOCUMENTS}${qs}`, {
      method: "DELETE",
    });
  },
};

