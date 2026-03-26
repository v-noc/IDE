import type { ActionContext } from "../../adapters/actionContext";
import type { HighlightCodeAction } from "../../types/walkthrough";

export async function highlightCodeHandler(
  action: HighlightCodeAction,
  ctx: ActionContext,
): Promise<void> {
  if (ctx.signal.aborted) return;

  ctx.adapter.highlightLines(action.nodeId, action.lines, action.style);

  ctx.cleanup.push(() => {
    ctx.adapter.clearHighlight(action.nodeId);
  });
}
