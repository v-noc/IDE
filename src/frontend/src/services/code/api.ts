import { api } from "@/lib/api";
import API_ROUTES from '@/lib/apiRoutes';

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  code: string;
}

function buildQueryString(params: Record<string, string>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== '') search.set(k, v);
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

export const codeApi = {
  getCode: (elementId: string, projectId: string): Promise<CodeData> => {
    const qs = buildQueryString({ node_id: elementId, project_id: projectId });
    return api(`${API_ROUTES.CODE_ELEMENTS}read-code/${qs}`);
  },
  writeCode: (elementId: string, code: string, projectId: string): Promise<void> => {
    const qs = buildQueryString({ node_id: elementId, project_id: projectId });
    return api(`${API_ROUTES.CODE_ELEMENTS}write-code${qs}`, {
      method: 'POST',
      body: { code },
    });
  },
}
