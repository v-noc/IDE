import type { ActionContext } from "../../adapters/actionContext";
import type { SelectNodeAction } from "../../types/walkthrough";

export async function selectNodeHandler(
  action: SelectNodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  const previousNodeId = ctx.adapter.getSelectedNodeId();
  ctx.adapter.selectNode(action.nodeId, action.selectionType);

  ctx.cleanup.push(() => {
    if (previousNodeId) {
      ctx.adapter.selectNode(previousNodeId, "primary");
    }
  });
}
