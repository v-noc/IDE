import type { ReactFlowInstance } from "@xyflow/react";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import type { WalkthroughStoreApi } from "../store/useWalkthroughStore";
import type { CanvasAdapter, PanOptions } from "./CanvasAdapter";
import type { HighlightStyle, LineRange } from "../types/walkthrough";

function mapSelectionType(
  t: "primary" | "secondary" | "promote",
): "primary" | "secondary" | "promte" {
  return t === "promote" ? "promte" : t;
}

export class ReactFlowCanvasAdapter implements CanvasAdapter {
  constructor(
    private readonly getTabId: () => string,
    private readonly getReactFlowInstance: () => ReactFlowInstance | null,
    private readonly projectStore: typeof useProjectStore,
    private readonly tabStore: typeof useTabStore,
    private readonly walkthroughStore: WalkthroughStoreApi,
  ) {}

  spotlightNode(nodeId: string): void {
    this.walkthroughStore.getState().setSpotlightNodeId(nodeId);
  }

  clearSpotlight(): void {
    this.walkthroughStore.getState().setSpotlightNodeId(null);
  }

  expandNode(nodeId: string): void {
    const tabId = this.getTabId();
    this.projectStore.getState().expandNode(tabId, nodeId);
  }

  collapseNode(nodeId: string): void {
    const tabId = this.getTabId();
    this.projectStore.getState().collapseNode(tabId, nodeId);
  }

  isNodeExpanded(nodeId: string): boolean {
    const tabId = this.getTabId();
    const expanded = this.projectStore.getState().expandedNodeIds[tabId] ?? [];
    return expanded.includes(nodeId);
  }

  showCode(nodeId: string): void {
    this.walkthroughStore.getState().setForcedCodeOpen(nodeId, true);
  }

  closeCode(nodeId: string): void {
    this.walkthroughStore.getState().setForcedCodeOpen(nodeId, false);
  }

  highlightLines(
    nodeId: string,
    lines: LineRange[],
    style?: HighlightStyle,
  ): void {
    this.walkthroughStore.getState().setHighlight(nodeId, lines, style);
  }

  clearHighlight(nodeId?: string): void {
    this.walkthroughStore.getState().clearHighlightStore(nodeId);
  }

  async panToNode(nodeId: string, options?: PanOptions): Promise<void> {
    const instance = this.getReactFlowInstance();
    if (!instance?.viewportInitialized) return;

    const duration = options?.duration ?? 300;
    const deadline = performance.now() + 12_000;

    while (performance.now() < deadline) {
      const target = instance.getNode(nodeId);
      const w = target?.measured?.width;
      if (target && w) {
        const h = target.measured?.height ?? 0;
        const zoom = options?.zoom ?? instance.getZoom();
        instance.setCenter(
          target.position.x + w / 2,
          target.position.y + h / 2,
          { zoom, duration },
        );
        await new Promise<void>((resolve) => {
          globalThis.setTimeout(resolve, duration);
        });
        return;
      }
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => resolve());
      });
    }
  }

  selectNode(
    nodeId: string,
    selectionType: "primary" | "secondary" | "promote",
  ): void {
    const tabId = this.getTabId();
    const projectData = this.projectStore.getState().projectData;
    if (!projectData) return;

    const node = findNodeByKey(projectData, nodeId);
    if (!node) return;

    this.tabStore
      .getState()
      .handleNodeSelection(tabId, node, mapSelectionType(selectionType));
  }

  getSelectedNodeId(): string | null {
    const tabId = this.getTabId();
    return this.projectStore.getState().selectedNode[tabId]?.id ?? null;
  }

  createTab(callNodeId: string): void {
    const tabId = this.getTabId();
    const projectData = this.projectStore.getState().projectData;
    if (!projectData) return;

    const node = findNodeByKey(projectData, callNodeId);
    if (!node) return;

    this.tabStore.getState().handleNodeSelection(tabId, node, "promte");
  }

  destroyTab(callNodeId: string): void {
    const tabId = this.getTabId();
    const currentTab = this.tabStore.getState().tabs[tabId];
    if (!currentTab) return;

    const childId = currentTab.childrenIds.find((id) => {
      const child = this.tabStore.getState().tabs[id];
      return child?.sourceCallNodeId === callNodeId;
    });

    if (childId) {
      this.tabStore.getState().destroyTabBranch(childId);
    }
  }

  getActiveTabId(): string {
    return this.tabStore.getState().activeTabId;
  }

  setActiveTab(tabId: string): void {
    this.tabStore.getState().setActiveTabId(tabId);
  }
}
