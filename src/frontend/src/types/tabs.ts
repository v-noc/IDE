import type { AnyNodeTree } from './project';

export interface TabData {
    id: string;
    title: string;
    parentId: string | null;
    /**
     * The ID of the CallNode in the PARENT tab that spawned this tab.
     * If null, this is the root tab.
     */
    sourceCallNodeId: string | null;
    childrenIds: string[];
    /**
     * The percentage size of the tab in the resizable stack.
     */
    layoutSize?: number;
}

export interface TabsSlice {
    tabs: Record<string, TabData>;
    rootTabId: string;
    activeTabId: string;

    // Actions
    addTab: (tab: TabData) => void;
    removeTab: (tabId: string) => void;
    setActiveTabId: (tabId: string) => void;
    /**
     * Destroys the given tab and ALL its descendants.
     */
    destroyTabBranch: (tabId: string) => void;
    /**
     * Updates the layout sizes for the given tabs.
     */
    updateTabLayouts: (layouts: { tabId: string; size: number }[]) => void;
    /**
     * High-level selection handler for the hierarchical tab system.

     */
    handleNodeSelection: (tabId: string, node: AnyNodeTree | null) => void;
}
