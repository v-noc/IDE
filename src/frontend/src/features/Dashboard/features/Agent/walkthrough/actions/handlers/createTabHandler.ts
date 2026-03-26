import type { ActionContext } from "../../adapters/actionContext";
import type { CreateTabAction } from "../../types/walkthrough";

export async function createTabHandler(
  action: CreateTabAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  const prevTabId = ctx.adapter.getActiveTabId();
  ctx.adapter.createTab(action.nodeId);

  ctx.cleanup.push(() => {
    ctx.adapter.destroyTab(action.nodeId);
    if (prevTabId) {
      ctx.adapter.setActiveTab(prevTabId);
    }
  });
}
