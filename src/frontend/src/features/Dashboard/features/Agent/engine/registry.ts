import type { ReplayEvent } from "../types/conversation";
import { clickHandler } from "./handlers/clickHandler";
import { focusHandler } from "./handlers/focusHandler";
import { waitHandler } from "./handlers/waitHandler";

export type ReplayHandler = (
  event: ReplayEvent,
  signal: AbortSignal,
) => Promise<void>;

export type ReplayRegistry = Partial<Record<ReplayEvent["type"], ReplayHandler>>;

export function createDefaultRegistry(): ReplayRegistry {
  return {
    wait: waitHandler,
    click: clickHandler,
    focus: focusHandler,
  };
}
