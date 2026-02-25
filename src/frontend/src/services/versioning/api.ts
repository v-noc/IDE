import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

function buildQueryString(params: Record<string, string | number>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== "") search.set(k, String(v));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

/** Backend commit response - matches CommitResponse from commits.py */
export interface Commit {
  id: string;
  message: string;
  timestamp: string; // ISO datetime from backend
  author: string;
}

export interface Branch {
  name?: string;
  "@type"?: string;
  [key: string]: unknown;
}

export type TerminusJsonDiff = Record<string, unknown> | unknown[];

export const versioningApi = {
  getBranches: (projectId: string): Promise<Branch[]> => {
    const qs = buildQueryString({ project_id: projectId });
    return api(`${API_ROUTES.VERSIONING}/branches${qs}`);
  },

  createBranch: (projectId: string, name: string): Promise<{ ok: boolean }> => {
    const qs = buildQueryString({ project_id: projectId, name });
    return api(`${API_ROUTES.VERSIONING}/branches${qs}`, {
      method: "POST",
      body: {},
    });
  },

  getCommits: (
    projectId: string,
    nodeId: string,
    options?: { start?: number; count?: number }
  ): Promise<Commit[]> => {
    const { start = 0, count = 10 } = options ?? {};
    const qs = buildQueryString({
      project_id: projectId,
      node_id: nodeId,
      start,
      count,
    });
    return api(`${API_ROUTES.VERSIONING}/commits${qs}`);
  },

  getDiff: (
    projectId: string,
    afterCommitId: string,
    beforeCommitId: string
  ): Promise<TerminusJsonDiff> => {
    const qs = buildQueryString({
      project_id: projectId,
      after_commit_id: afterCommitId,
      before_commit_id: beforeCommitId,
    });
    return api(`${API_ROUTES.VERSIONING}/commits/diff${qs}`);
  },
};
