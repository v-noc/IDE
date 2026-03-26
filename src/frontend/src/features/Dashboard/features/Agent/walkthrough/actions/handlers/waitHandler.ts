import type { ActionContext } from "../../adapters/actionContext";
import type { WaitAction } from "../../types/walkthrough";

/** Wall-clock wait is enforced by StepExecutor using `action.ms`. */
export async function waitHandler(
  _action: WaitAction,
  _ctx: ActionContext,
): Promise<void> {}
