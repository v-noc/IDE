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

async function apiClient<T>(
  endpoint: string,
  options: JsonRequestInit = {}
): Promise<T> {
  const { headers, body, ...customConfig } = options as JsonRequestInit;

  const config: RequestInit = {
    method: body ? 'POST' : 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    ...customConfig,
  };

  if (body !== undefined) {
    config.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

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
