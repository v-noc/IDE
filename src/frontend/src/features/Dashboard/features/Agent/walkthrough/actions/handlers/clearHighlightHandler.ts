import type { ActionContext } from "../../adapters/actionContext";
import type { ClearHighlightAction } from "../../types/walkthrough";

export async function clearHighlightHandler(
  action: ClearHighlightAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;
  ctx.adapter.clearHighlight(action.nodeId);
}
