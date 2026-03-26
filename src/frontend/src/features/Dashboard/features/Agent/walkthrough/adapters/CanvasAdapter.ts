import type { HighlightStyle, LineRange } from "../types/walkthrough";

export interface PanOptions {
  duration?: number;
  zoom?: number;
}

/**
 * Boundary between the walkthrough engine and canvas / project state.
 * Handlers call adapter methods only — never the DOM or stores directly.
 */
export interface CanvasAdapter {
  spotlightNode(nodeId: string): void;
  clearSpotlight(): void;

  expandNode(nodeId: string): void;
  collapseNode(nodeId: string): void;
  isNodeExpanded(nodeId: string): boolean;

  highlightLines(
    nodeId: string,
    lines: LineRange[],
    style?: HighlightStyle,
  ): void;
  clearHighlight(nodeId?: string): void;

  panToNode(nodeId: string, options?: PanOptions): Promise<void>;

  selectNode(
    nodeId: string,
    selectionType: "primary" | "secondary" | "promote",
  ): void;
  getSelectedNodeId(): string | null;

  createTab(callNodeId: string): void;
  destroyTab(callNodeId: string): void;
  getActiveTabId(): string;
  setActiveTab(tabId: string): void;
}
