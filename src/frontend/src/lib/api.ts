import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

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
};

async function apiClient<T>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const {
    headers,
    body,
    branch: branchOverride,
    ref: refOverride,
    ...customConfig
  } = options as ApiRequestOptions;
  const state = useVersioningStore.getState();
  const branch = branchOverride ?? state.branch;
  const ref = refOverride ?? state.checkedOutCommitId ?? undefined;
  let finalEndpoint = endpoint;
  if (ref) {
    const separator = finalEndpoint.includes("?") ? "&" : "?";
    finalEndpoint = `${finalEndpoint}${separator}ref=${encodeURIComponent(ref)}`;
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
