import { api } from "@/lib/api";
import API_ROUTES from '@/lib/apiRoutes';

export interface DocumentData {
  id: string;
  name: string;
  description: string;
  data: string;
  /** Markdown export for AI / text consumers; may mirror editor JSON until optimized. */
  markdown: string;
  created_at: string;
  updated_at: string;
  status?: "added" | "removed" | "modified" | "unchanged" | "none";
  compare_to?: DocumentData | null;
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
  markdown?: string;
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
  markdown?: string;
  created_at: string;
  updated_at: string;
  status?: "added" | "removed" | "modified" | "unchanged" | "none";
  compare_to?: BackendDocumentRaw | null;
}

interface BackendDocumentsResponse {
  documents?: BackendDocumentRaw[];
  compare_to?: BackendDocumentRaw[] | BackendDocumentRaw | null;
}

const mapBackendDocument = (d: BackendDocumentRaw): DocumentData => {
  const compareToMapped = d.compare_to ? mapBackendDocument(d.compare_to) : null;
  return {
    id: d.id ?? "",
    name: d.name,
    description: d.description,
    data: d.data,
    markdown: d.markdown ?? "",
    created_at: d.created_at,
    updated_at: d.updated_at,
    status: d.status,
    compare_to: compareToMapped,
  };
};

function getDocumentMatchKey(d: BackendDocumentRaw): string {
  return d.id ?? `${d.name}::${d.description}`;
}

export const documentsApi = {
  getDocuments: async (nodeId: string, projectId: string): Promise<DocumentData[]> => {
    const qs = buildQueryString({ node_id: nodeId, project_id: projectId });
    const response = await api(`${API_ROUTES.DOCUMENTS}${qs}`);
    // Supports both legacy list response and compare-aware response.
    if (Array.isArray(response)) {
      const list = response as BackendDocumentRaw[];
      return list.map(mapBackendDocument);
    }

    const payload = response as BackendDocumentsResponse;
    const documents = Array.isArray(payload.documents) ? payload.documents : [];
    const rawCompare = payload.compare_to;
    const compareList = Array.isArray(rawCompare)
      ? rawCompare
      : rawCompare
        ? [rawCompare]
        : [];

    const compareByKey = new Map<string, BackendDocumentRaw>();
    for (const compareDoc of compareList) {
      compareByKey.set(getDocumentMatchKey(compareDoc), compareDoc);
    }

    return documents.map((doc) => {
      const key = getDocumentMatchKey(doc);
      const mapped = mapBackendDocument(doc);
      const compareDoc = compareByKey.get(key);
      return {
        ...mapped,
        compare_to: compareDoc ? mapBackendDocument(compareDoc) : null,
      };
    });
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
      markdown: payload.markdown,
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

