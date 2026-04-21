import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { blockWriteIfReadOnly } from "@/lib/readOnlyGate";
import { isWriteHttpMethod } from "@/lib/readOnlyMode";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiError extends Error {
  status: number;
  response: unknown;
  constructor(message: string, status: number, response: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

type JsonRequestInit = Omit<RequestInit, "body"> & { body?: unknown };
type ApiRequestOptions = JsonRequestInit & {
  branch?: string;
  ref?: string;
  compareTo?: string;
};

function normalizeCommitId(commitId?: string | null): string | undefined {
  if (!commitId) return undefined;
  return commitId.startsWith("branch:") ? commitId.slice("branch:".length) : commitId;
}

async function apiClient<T>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const {
    headers,
    body,
    branch: branchOverride,
    ref: refOverride,
    compareTo: compareToOverride,
    ...customConfig
  } = options as ApiRequestOptions;

  const resolvedMethod =
    typeof customConfig.method === "string"
      ? customConfig.method
      : body !== undefined
        ? "POST"
        : "GET";
  if (isWriteHttpMethod(resolvedMethod)) {
    blockWriteIfReadOnly();
  }

  const state = useVersioningStore.getState();
  const branch = branchOverride ?? state.branch;
  const ref = normalizeCommitId(refOverride ?? state.checkedOutCommitId ?? undefined);
  const compareTo = normalizeCommitId(compareToOverride ?? state.compareToCommitId ?? undefined);
  let finalEndpoint = endpoint;
  if (ref) {
    const separator = finalEndpoint.includes("?") ? "&" : "?";
    finalEndpoint = `${finalEndpoint}${separator}ref=${encodeURIComponent(ref)}`;
  }
  if (compareTo) {
    const separator = finalEndpoint.includes("?") ? "&" : "?";
    finalEndpoint = `${finalEndpoint}${separator}compare_to=${encodeURIComponent(compareTo)}`;
  }

  const config: RequestInit = {
    method: body ? 'POST' : 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(branch ? { "X-Vnoc-Branch": branch } : {}),
      ...headers,
    },
    ...customConfig,
  };

  if (body !== undefined) {
    config.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${finalEndpoint}`, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status,
      errorData
    );
  }

  // Handle 204 No Content response
  if (response.status === 204) {
    return Promise.resolve(undefined as T);
  }

  return response.json();
}

export { apiClient as api };
