import { applyOperation } from "fast-json-patch";
import type { Operation } from "fast-json-patch";
import type { Frame, WalkthroughPhase, WalkthroughSession } from "../types";
import { parseFrame } from "../types";

export interface FrameApplyResult {
  session: WalkthroughSession | null;
  lastSeq: number;
  phase: WalkthroughPhase;
  error: string | null;
}

export function applyOpsToSession(
  session: WalkthroughSession,
  ops: Operation[],
): WalkthroughSession {
  const clone = structuredClone(session);
  for (const op of ops) {
    applyOperation(clone, op, /* validateOperation */ false, /* mutate */ true);
  }
  return clone;
}

export function applyFrame(
  frame: Frame,
  current: {
    session: WalkthroughSession | null;
    lastSeq: number;
    phase: WalkthroughPhase;
  },
): FrameApplyResult {
  switch (frame.kind) {
    case "hello":
      return {
        session: frame.session,
        lastSeq: -1,
        phase: "generating",
        error: null,
      };

    case "patch": {
      if (!current.session) {
        return {
          session: null,
          lastSeq: current.lastSeq,
          phase: "error",
          error: "patch before hello",
        };
      }

      if (frame.seq <= current.lastSeq) {
        console.warn(
          `[walkthrough] stale patch seq=${frame.seq}, last=${current.lastSeq}`,
        );
        return {
          session: current.session,
          lastSeq: current.lastSeq,
          phase: current.phase,
          error: null,
        };
      }

      if (frame.seq > current.lastSeq + 1) {
        console.warn(
          `[walkthrough] patch gap: expected ${current.lastSeq + 1}, got ${frame.seq}`,
        );
      }

      return {
        session: applyOpsToSession(current.session, frame.ops),
        lastSeq: frame.seq,
        phase: current.phase === "idle" ? "generating" : current.phase,
        error: null,
      };
    }

    case "end":
      if (frame.status === "error") {
        return {
          session: current.session,
          lastSeq: current.lastSeq,
          phase: "error",
          error: frame.message ?? "Generation failed",
        };
      }

      return {
        session: current.session
          ? { ...current.session, status: "complete" }
          : null,
        lastSeq: current.lastSeq,
        phase: current.phase === "playing" ? "playing" : "ready",
        error: null,
      };
  }
}

export function parseAndApplyFrame(
  raw: unknown,
  current: {
    session: WalkthroughSession | null;
    lastSeq: number;
    phase: WalkthroughPhase;
  },
): FrameApplyResult | null {
  const frame = parseFrame(raw);
  if (!frame) return null;
  return applyFrame(frame, current);
}
