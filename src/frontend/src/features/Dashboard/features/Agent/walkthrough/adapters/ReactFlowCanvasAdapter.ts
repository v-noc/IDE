import type { CanvasAdapter, PanOptions } from "./CanvasAdapter";
import type { HighlightStyle, LineRange } from "../types/walkthrough";

/**
 * Stub adapter for early integration. Replace with store + React Flow wiring
 * per doc/walkthrough-plan/05-canvas-adapter.md.
 */
export class ReactFlowCanvasAdapter implements CanvasAdapter {
  spotlightNode(_nodeId: string): void {}

  clearSpotlight(): void {}

  expandNode(_nodeId: string): void {}

  collapseNode(_nodeId: string): void {}

  isNodeExpanded(_nodeId: string): boolean {
    return false;
  }

  highlightLines(
    _nodeId: string,
    _lines: LineRange[],
    _style?: HighlightStyle,
  ): void {}

  clearHighlight(_nodeId?: string): void {}

  async panToNode(_nodeId: string, _options?: PanOptions): Promise<void> {}

  selectNode(
    _nodeId: string,
    _selectionType: "primary" | "secondary" | "promote",
  ): void {}

  getSelectedNodeId(): string | null {
    return null;
  }

  createTab(_callNodeId: string): void {}

  destroyTab(_callNodeId: string): void {}

  getActiveTabId(): string {
    return "";
  }

  setActiveTab(_tabId: string): void {}
}
