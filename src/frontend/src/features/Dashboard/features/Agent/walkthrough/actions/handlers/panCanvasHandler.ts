import type { ActionContext } from "../../adapters/actionContext";
import type { PanCanvasAction } from "../../types/walkthrough";

export async function panCanvasHandler(
  action: PanCanvasAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  await ctx.adapter.panToNode(action.to.nodeId, { duration: 300 });
}
