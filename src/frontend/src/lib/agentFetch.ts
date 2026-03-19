import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export class AgentHttpError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body: unknown,
  ) {
    super(message);
    this.name = "AgentHttpError";
  }
}

export type AgentFetchInit = Omit<RequestInit, "body"> & { body?: unknown };

function normalizeCommitId(commitId?: string | null): string | undefined {
  if (!commitId) return undefined;
  return commitId.startsWith("branch:") ? commitId.slice("branch:".length) : commitId;
}

/** Append project + versioning query params (same contract as `@/lib/api`). */
function appendProjectAndVersioningQuery(path: string, projectId: string): string {
  const state = useVersioningStore.getState();
  const ref = normalizeCommitId(state.checkedOutCommitId ?? undefined);
  const compareTo = normalizeCommitId(state.compareToCommitId ?? undefined);

  const params = new URLSearchParams();
  params.set("project_id", projectId);
  if (ref) params.set("ref", ref);
  if (compareTo) params.set("compare_to", compareTo);

  const suffix = params.toString();
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}${suffix}`;
}

export async function agentFetch<T>(
  path: string,
  init: AgentFetchInit = {},
  projectId: string,
): Promise<T> {
  if (!projectId) {
    throw new AgentHttpError("Missing projectId for agent request", 0, {});
  }

  const finalPath = appendProjectAndVersioningQuery(path, projectId);
  const branch = useVersioningStore.getState().branch;

  const { body, headers, ...rest } = init;
  const res = await fetch(`${API_BASE_URL}${finalPath}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(branch ? { "X-Vnoc-Branch": branch } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new AgentHttpError(res.statusText, res.status, errBody);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
