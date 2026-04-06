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
  id: string;
  name: string;
  is_current: boolean;
  head_commit: string;
}

export type TerminusJsonDiff = Record<string, unknown> | unknown[];

export type VersioningRemoteAuth = {
  type: string;
  username?: string | null;
  key: string;
};

type VersioningRequestContext = {
  branch?: string;
  ref?: string;
};

export const versioningApi = {
  getBranches: (
    projectId: string,
    context?: VersioningRequestContext
  ): Promise<Branch[]> => {
    const qs = buildQueryString({ project_id: projectId });
    return api(`${API_ROUTES.VERSIONING}/branches${qs}`, context);
  },

  createBranch: (
    projectId: string,
    name: string,
    context?: VersioningRequestContext
  ): Promise<{ ok: boolean }> => {
    const qs = buildQueryString({ project_id: projectId });
    return api(`${API_ROUTES.VERSIONING}/branches${qs}`, {
      method: "POST",
      body: { name },
      ...context,
    });
  },

  getCommits: (
    projectId: string,
    nodeId: string,
    options?: { start?: number; count?: number; branch?: string; ref?: string }
  ): Promise<Commit[]> => {
    const { start = 0, count = 10, branch, ref } = options ?? {};
    const qs = buildQueryString({
      project_id: projectId,
      node_id: nodeId,
      start,
      count,
    });
    return api(`${API_ROUTES.VERSIONING}/commits/${qs}`, { branch, ref });
  },

  getDiff: (
    projectId: string,
    afterCommitId: string,
    beforeCommitId: string,
    context?: VersioningRequestContext
  ): Promise<TerminusJsonDiff> => {
    const qs = buildQueryString({
      project_id: projectId,
      after_commit_id: afterCommitId,
      before_commit_id: beforeCommitId,
    });
    return api(`${API_ROUTES.VERSIONING}/commits/diff${qs}`, context);
  },

  push: (
    projectId: string,
    body: {
      remote?: string;
      branch?: string | null;
      remote_branch?: string | null;
      remote_auth: VersioningRemoteAuth;
    },
    context?: VersioningRequestContext
  ): Promise<Record<string, unknown>> => {
    const qs = buildQueryString({ project_id: projectId });
    return api(`${API_ROUTES.VERSIONING}/remotes/push${qs}`, {
      method: "POST",
      body,
      ...context,
    });
  },

  pull: (
    projectId: string,
    body: {
      remote?: string;
      branch?: string | null;
      remote_branch?: string | null;
      remote_auth: VersioningRemoteAuth;
    },
    context?: VersioningRequestContext
  ): Promise<Record<string, unknown>> => {
    const qs = buildQueryString({ project_id: projectId });
    return api(`${API_ROUTES.VERSIONING}/remotes/pull${qs}`, {
      method: "POST",
      body,
      ...context,
    });
  },
};
