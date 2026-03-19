/**
 * REST calls for the agent namespace without versioning (`ref` / `X-Vnoc-Branch`) headers,
 * which would break Terminus-backed conversation routes.
 */

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

export async function agentFetch<T>(
  path: string,
  init: AgentFetchInit = {},
): Promise<T> {
  const { body, headers, ...rest } = init;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
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
