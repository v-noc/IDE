import type { ActionHandler } from "../adapters/actionContext";
import type { Action } from "../types/walkthrough";
import { ActionHandlerRegistry } from "./ActionHandlerRegistry";

const ACTION_TYPES: Action["type"][] = [
  "focus-node",
  "expand-node",
  "collapse-node",
  "show-code",
  "close-code",
  "highlight-code",
  "clear-highlight",
  "pan-canvas",
  "select-node",
  "create-tab",
  "wait",
];

const noop: ActionHandler = async () => {};

/** Registry where every action is a no-op — useful until real handlers are wired. */
export function createNoopActionRegistry(): ActionHandlerRegistry {
  const registry = new ActionHandlerRegistry();
  for (const type of ACTION_TYPES) {
    registry.register(type, noop);
  }
  return registry;
}
