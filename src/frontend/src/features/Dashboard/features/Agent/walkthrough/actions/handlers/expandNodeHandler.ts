import type { ActionContext } from "../../adapters/actionContext";
import type { ExpandNodeAction } from "../../types/walkthrough";

export async function expandNodeHandler(
  action: ExpandNodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  const wasExpanded = ctx.adapter.isNodeExpanded(action.nodeId);
  ctx.adapter.expandNode(action.nodeId);

  ctx.cleanup.push(() => {
    if (!wasExpanded) {
      ctx.adapter.collapseNode(action.nodeId);
    }
  });
}
