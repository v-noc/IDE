import type { ActionContext } from "../../adapters/actionContext";
import type { ShowCodeAction } from "../../types/walkthrough";

export async function showCodeHandler(
  action: ShowCodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  ctx.adapter.showCode(action.nodeId);

  ctx.cleanup.push(() => {
    ctx.adapter.closeCode(action.nodeId);
  });
}
