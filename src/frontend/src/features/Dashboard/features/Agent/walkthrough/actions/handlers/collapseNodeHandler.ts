import type { ActionContext } from "../../adapters/actionContext";
import type { CollapseNodeAction } from "../../types/walkthrough";

export async function collapseNodeHandler(
  action: CollapseNodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;
  ctx.adapter.collapseNode(action.nodeId);
}
