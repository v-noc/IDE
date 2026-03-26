import type { ActionContext } from "../../adapters/actionContext";
import type { FocusNodeAction } from "../../types/walkthrough";

export async function focusNodeHandler(
  action: FocusNodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  ctx.adapter.spotlightNode(action.nodeId);

  ctx.cleanup.push(() => {
    ctx.adapter.clearSpotlight();
  });
}
