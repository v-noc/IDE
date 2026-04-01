import { api } from "@/lib/api";
import API_ROUTES from '@/lib/apiRoutes';

export type CodeDescendantsResponse = {
  /** Nested code tree roots under the requested parent (same shape as project tree nodes). */
  children: Record<string, unknown>[];
};

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  content_id?: string;
  position?: {
    line_no: number;
    col_offset: number;
    end_line_no: number | null;
    end_col_offset: number | null;
  } | null;
  code: string;
  compare_to?: CodeData;
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

  getDescendants: (
    projectId: string,
    parentId: string,
    opts?: {
      depthStart?: number;
      depthMax?: number;
      childTypes?: string;
      compareTo?: string | null;
    }
  ): Promise<CodeDescendantsResponse> => {
    const params: Record<string, string> = {
      project_id: projectId,
      parent_id: parentId,
    };
    if (opts?.depthStart != null) params.depth_start = String(opts.depthStart);
    if (opts?.depthMax != null) params.depth_max = String(opts.depthMax);
    if (opts?.childTypes) params.child_types = opts.childTypes;
    const qs = buildQueryString(params);
    return api(`${API_ROUTES.CODE_ELEMENTS}descendants${qs}`, {
      compareTo: opts?.compareTo ?? undefined,
    }) as Promise<CodeDescendantsResponse>;
  },
}
