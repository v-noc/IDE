import type { Action } from "../types/walkthrough";
import type { CanvasAdapter } from "./CanvasAdapter";

/** Teardown sink passed into handlers (see engine `CleanupStack`). */
export interface ActionCleanupSink {
  push(fn: () => void): void;
}

export interface ActionContext {
  adapter: CanvasAdapter;
  signal: AbortSignal;
  cleanup: ActionCleanupSink;
}

export type ActionHandler<T extends Action = Action> = (
  action: T,
  ctx: ActionContext,
) => Promise<void>;
