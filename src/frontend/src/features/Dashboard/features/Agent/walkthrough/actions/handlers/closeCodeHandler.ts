import type { ActionContext } from "../../adapters/actionContext";
import type { CloseCodeAction } from "../../types/walkthrough";

export async function closeCodeHandler(
  action: CloseCodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;
  ctx.adapter.closeCode(action.nodeId);
}
