import type { Estimate, Frame } from "../types";
import { parseFrame } from "../types";
import type { WalkthroughSource } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export function parseNdjsonChunk(
  buffer: string,
  onFrame: (frame: Frame) => void,
): string {
  const lines = buffer.split("\n");
  const remainder = lines.pop() ?? "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    try {
      const raw = JSON.parse(trimmed) as unknown;
      const frame = parseFrame(raw);
      if (frame) onFrame(frame);
    } catch {
      console.warn("[walkthrough] bad frame line", line);
    }
  }

  return remainder;
}

export function parseNdjsonTail(
  tail: string,
  onFrame: (frame: Frame) => void,
): void {
  const trimmed = tail.trim();
  if (!trimmed) return;

  try {
    const frame = parseFrame(JSON.parse(trimmed) as unknown);
    if (frame) onFrame(frame);
  } catch {
    console.warn("[walkthrough] bad frame line", tail);
  }
}

export const httpSource: WalkthroughSource = {
  async estimate(req) {
    const params = new URLSearchParams({
      node_id: req.node_id,
      depth: String(req.depth),
      project_id: req.project_id,
    });

    const res = await fetch(`${API_BASE}/walkthroughs/estimate?${params}`);
    if (!res.ok) {
      throw new Error(`Estimate failed: ${res.status}`);
    }

    return (await res.json()) as Estimate;
  },

  async run(req, onFrame, signal) {
    const res = await fetch(`${API_BASE}/walkthroughs/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal,
    });

    if (!res.ok || !res.body) {
      throw new Error(`Run failed: ${res.status}`);
    }

    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += value;
      buffer = parseNdjsonChunk(buffer, onFrame);
    }

    parseNdjsonTail(buffer, onFrame);
  },
};
