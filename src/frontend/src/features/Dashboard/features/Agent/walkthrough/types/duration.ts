import type { Action, WalkthroughStep } from "./walkthrough";

export const TYPEWRITER_MS_PER_CHAR = 30;
export const DEFAULT_POST_POPOVER_PAUSE = 500;

export function getDefaultDuration(type: Action["type"]): number {
  switch (type) {
    case "focus-node":
      return 500;
    case "expand-node":
      return 400;
    case "collapse-node":
      return 400;
    case "show-code":
      return 600;
    case "close-code":
      return 400;
    case "highlight-code":
      return 300;
    case "clear-highlight":
      return 200;
    case "pan-canvas":
      return 500;
    case "select-node":
      return 300;
    case "create-tab":
      return 800;
    case "wait":
      return 0;
    default: {
      const _exhaustive: never = type;
      return _exhaustive;
    }
  }
}

/** Total duration of one step (actions + typewriter + post-popover pause). */
export function computeStepDuration(step: WalkthroughStep): number {
  const actionsDuration = step.actions.reduce((sum, action) => {
    const d =
      action.type === "wait"
        ? action.ms
        : (action.duration ?? getDefaultDuration(action.type));
    return sum + d;
  }, 0);

  const typewriterDuration = step.popover
    ? step.popover.body.length * TYPEWRITER_MS_PER_CHAR
    : 0;

  const postPause = step.popover ? DEFAULT_POST_POPOVER_PAUSE : 0;

  return actionsDuration + typewriterDuration + postPause;
}
