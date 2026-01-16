import type { StateCreator } from 'zustand';
import type { TabsSlice, TabData } from '@/types/tabs';
export type { TabsSlice, TabData };
import type { SelectionSlice } from './selectionSlice';
import type { FocusSlice } from './focusSlice';
import type { UISlice } from './uiSlice';
import type { DataSlice } from './dataSlice';

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice & TabsSlice;

export const createTabsSlice: StateCreator<
    ProjectStore,
    [['zustand/immer', never], ['zustand/devtools', never]],
    [],
    TabsSlice
> = (set, get) => ({
    tabs: {
        root: {
            id: 'root',
            title: 'Main',
            parentId: null,
            sourceCallNodeId: null,
            childrenIds: [],
        },
    },
    rootTabId: 'root',
    activeTabId: 'root',

    addTab: (tab: TabData) =>
        set((state: ProjectStore) => {
            state.tabs[tab.id] = tab;
            if (tab.parentId && state.tabs[tab.parentId]) {
                state.tabs[tab.parentId].childrenIds.push(tab.id);
            }
        }),

    removeTab: (tabId: string) =>
        set((state: ProjectStore) => {
            const tab = state.tabs[tabId];
            if (!tab) return;

            // Unlink from parent
            if (tab.parentId && state.tabs[tab.parentId]) {
                state.tabs[tab.parentId].childrenIds = state.tabs[tab.parentId].childrenIds.filter(
                    (id: string) => id !== tabId
                );
            }

            // Cleanup slice data for this tab
            delete state.focusStack[tabId];
            delete state.focusedNode[tabId];
            delete state.focusTargetId[tabId];
            delete state.selectedNode[tabId];
            delete state.secondarySelectedNode[tabId];
            delete state.selectedDocumentId[tabId];
            delete state.expandedNodeIds[tabId];
            delete state.activeNodeId[tabId];

            delete state.tabs[tabId];

            // If we removed the active tab, switch back to root
            if (state.activeTabId === tabId) {
                state.activeTabId = state.rootTabId;
            }
        }),

    setActiveTabId: (tabId: string) =>
        set((state: ProjectStore) => {
            state.activeTabId = tabId;
        }),

    destroyTabBranch: (tabId: string) => {
        const tab = get().tabs[tabId];
        if (!tab) return;

        // Destroy children first (recursive)
        tab.childrenIds.forEach((childId: string) => {
            get().destroyTabBranch(childId);
        });

        // Remove this tab (which also cleans up its slice state)
        get().removeTab(tabId);
    },

    handleNodeSelection: (tabId, node) => {
        const state = get();
        const currentTab = state.tabs[tabId];

        if (!currentTab) return;

        // 1. Destroy existing children branch
        currentTab.childrenIds.forEach((childId) => {
            state.destroyTabBranch(childId);
        });

        // 2. Update selection for the current tab
        state.setSelectedNode(tabId, node);

        // 3. If it's a CallNode, create a new child tab (Portal)
        if (node && node.node_type === 'call') {
            const callNode = node as any; // Cast as ANY for now to avoid complex tree vs node issues
            const target = callNode.target;

            if (target) {
                const newTabId = crypto.randomUUID();
                const newTab: TabData = {
                    id: newTabId,
                    title: `Explore: ${target.name}`,
                    parentId: tabId,
                    sourceCallNodeId: node._key,
                    childrenIds: [],
                };

                // Add the tab
                state.addTab(newTab);

                // Initialize the new tab's focus stack with the target
                state.pushFocus(newTabId, target as any);

                // Auto-activate the new tab
                state.setActiveTabId(newTabId);
            }
        }
    },
});
