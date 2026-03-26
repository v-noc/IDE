import { ActionHandlerRegistry } from "./ActionHandlerRegistry";
import { clearHighlightHandler } from "./handlers/clearHighlightHandler";
import { closeCodeHandler } from "./handlers/closeCodeHandler";
import { collapseNodeHandler } from "./handlers/collapseNodeHandler";
import { createTabHandler } from "./handlers/createTabHandler";
import { expandNodeHandler } from "./handlers/expandNodeHandler";
import { focusNodeHandler } from "./handlers/focusNodeHandler";
import { highlightCodeHandler } from "./handlers/highlightCodeHandler";
import { panCanvasHandler } from "./handlers/panCanvasHandler";
import { selectNodeHandler } from "./handlers/selectNodeHandler";
import { showCodeHandler } from "./handlers/showCodeHandler";
import { waitHandler } from "./handlers/waitHandler";

export function createDefaultRegistry(): ActionHandlerRegistry {
  return new ActionHandlerRegistry()
    .register("focus-node", focusNodeHandler)
    .register("expand-node", expandNodeHandler)
    .register("collapse-node", collapseNodeHandler)
    .register("show-code", showCodeHandler)
    .register("close-code", closeCodeHandler)
    .register("highlight-code", highlightCodeHandler)
    .register("clear-highlight", clearHighlightHandler)
    .register("pan-canvas", panCanvasHandler)
    .register("select-node", selectNodeHandler)
    .register("create-tab", createTabHandler)
    .register("wait", waitHandler);
}
