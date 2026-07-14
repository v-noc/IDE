import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import type { Conversation, ConversationSummary, Part, WireFrame } from "./types";
import { parseWireFrame } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

function branchHeaders(): HeadersInit {
  const branch = useVersioningStore.getState().branch;
  return branch ? { "X-Vnoc-Branch": branch } : {};
}

function withProject(path: string, projectId: string): string {
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}project_id=${encodeURIComponent(projectId)}`;
}

/** Leave Terminus ids like `ConversationSchema/<uuid>` as path segments. */
function conversationPath(conversationId: string): string {
  return `${API_BASE}/conversations/${conversationId}`;
}

export function parseNdjsonChunk(
  buffer: string,
  onFrame: (frame: WireFrame) => void,
): string {
  const lines = buffer.split("\n");
  const remainder = lines.pop() ?? "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      const frame = parseWireFrame(JSON.parse(trimmed) as unknown);
      if (frame) onFrame(frame);
    } catch {
      console.warn("[agent] bad frame line", line);
    }
  }

  return remainder;
}

export function parseNdjsonTail(
  tail: string,
  onFrame: (frame: WireFrame) => void,
): void {
  const trimmed = tail.trim();
  if (!trimmed) return;
  try {
    const frame = parseWireFrame(JSON.parse(trimmed) as unknown);
    if (frame) onFrame(frame);
  } catch {
    console.warn("[agent] bad frame line", tail);
  }
}

/**
 * Buffer frames and flush to `onFrames` once per animation frame.
 * Token appends still look live (~16ms) without store thrash.
 */
export function createRafDispatcher(
  onFrames: (frames: WireFrame[]) => void,
): {
  push: (frame: WireFrame) => void;
  flush: () => void;
  dispose: () => void;
} {
  let buffer: WireFrame[] = [];
  let raf: number | null = null;

  const flush = () => {
    if (raf != null) {
      cancelAnimationFrame(raf);
      raf = null;
    }
    if (buffer.length === 0) return;
    const batch = buffer;
    buffer = [];
    onFrames(batch);
  };

  const push = (frame: WireFrame) => {
    buffer.push(frame);
    if (raf != null) return;
    raf = requestAnimationFrame(() => {
      raf = null;
      flush();
    });
  };

  const dispose = () => {
    if (raf != null) {
      cancelAnimationFrame(raf);
      raf = null;
    }
    buffer = [];
  };

  return { push, flush, dispose };
}

export async function createConversation(
  projectId: string,
): Promise<Conversation> {
  const res = await fetch(
    withProject(`${API_BASE}/conversations`, projectId),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...branchHeaders(),
      },
    },
  );
  if (!res.ok) {
    throw new Error(`Create conversation failed: ${res.status}`);
  }
  return (await res.json()) as Conversation;
}

export async function listConversations(
  projectId: string,
  opts?: { limit?: number; offset?: number },
): Promise<ConversationSummary[]> {
  const params = new URLSearchParams({
    project_id: projectId,
    limit: String(opts?.limit ?? 50),
    offset: String(opts?.offset ?? 0),
  });
  const res = await fetch(`${API_BASE}/conversations?${params}`, {
    headers: branchHeaders(),
  });
  if (!res.ok) {
    throw new Error(`List conversations failed: ${res.status}`);
  }
  return (await res.json()) as ConversationSummary[];
}

export async function getConversation(
  projectId: string,
  conversationId: string,
): Promise<Conversation> {
  const res = await fetch(
    withProject(conversationPath(conversationId), projectId),
    { headers: branchHeaders() },
  );
  if (!res.ok) {
    throw new Error(`Get conversation failed: ${res.status}`);
  }
  return (await res.json()) as Conversation;
}

export async function getArtifact(
  projectId: string,
  conversationId: string,
  doc: string,
): Promise<unknown> {
  const res = await fetch(
    withProject(
      `${conversationPath(conversationId)}/artifacts/${doc}`,
      projectId,
    ),
    { headers: branchHeaders() },
  );
  if (!res.ok) {
    throw new Error(`Get artifact failed: ${res.status}`);
  }
  return res.json();
}

export async function cancelRun(
  projectId: string,
  conversationId: string,
): Promise<void> {
  const res = await fetch(
    withProject(`${conversationPath(conversationId)}/cancel`, projectId),
    {
      method: "POST",
      headers: branchHeaders(),
    },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`Cancel failed: ${res.status}`);
  }
}

export async function postDecision(
  projectId: string,
  conversationId: string,
  body: {
    tool_call_id: string;
    decision: "approve" | "cancel";
    overrides?: Record<string, unknown>;
  },
): Promise<void> {
  const res = await fetch(
    withProject(`${conversationPath(conversationId)}/decision`, projectId),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...branchHeaders(),
      },
      body: JSON.stringify(body),
    },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`Decision failed: ${res.status}`);
  }
}

export async function streamMessage(
  projectId: string,
  conversationId: string,
  parts: Part[],
  onFrames: (frames: WireFrame[]) => void,
  signal?: AbortSignal,
  options?: { effort?: string },
): Promise<void> {
  const dispatcher = createRafDispatcher(onFrames);

  try {
    const res = await fetch(
      withProject(`${conversationPath(conversationId)}/messages`, projectId),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...branchHeaders(),
        },
        body: JSON.stringify({
          parts,
          options: options?.effort ? { effort: options.effort } : undefined,
        }),
        signal,
      },
    );

    if (!res.ok || !res.body) {
      throw new Error(`Send message failed: ${res.status}`);
    }

    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;
      buffer = parseNdjsonChunk(buffer, dispatcher.push);
    }
    parseNdjsonTail(buffer, dispatcher.push);
    dispatcher.flush();
  } finally {
    dispatcher.dispose();
  }
}
