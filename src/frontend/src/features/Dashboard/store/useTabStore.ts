import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { TabData } from '@/types/tabs';
import type { AnyNodeTree } from '@/types/project';
import useProjectStore from './useProjectStore';
import { findNodeLineage } from '../utils/findNode';

export interface TabState {
  tabs: Record<string, TabData>;
  rootTabId: string;
  activeTabId: string;
}

export interface TabActions {
  addTab: (tab: TabData) => void;
  removeTab: (tabId: string) => void;
  setActiveTabId: (tabId: string) => void;
  destroyTabBranch: (tabId: string) => void;
  handleNodeSelection: (tabId: string, node: any) => void;
}

export type TabStore = TabState & TabActions;

const useTabStore = create<TabStore>()(
  devtools(
    immer((set, get) => ({
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
        set((state) => {
          console.log("addTab", tab);
          state.tabs[tab.id] = tab;
          if (tab.parentId && state.tabs[tab.parentId]) {
            state.tabs[tab.parentId].childrenIds.push(tab.id);
          }
        }),

      removeTab: (tabId: string) =>
        set((state) => {
          const tab = state.tabs[tabId];
          if (!tab) return;

          // Unlink from parent
          if (tab.parentId && state.tabs[tab.parentId]) {
            state.tabs[tab.parentId].childrenIds = state.tabs[tab.parentId].childrenIds.filter(
              (id: string) => id !== tabId
            );
          }

          // Cleanup slice data for this tab in project store
          useProjectStore.getState().cleanupTabData(tabId);

          delete state.tabs[tabId];

          // If we removed the active tab, switch back to root
          if (state.activeTabId === tabId) {
            state.activeTabId = state.rootTabId;
          }
        }),

      setActiveTabId: (tabId: string) =>
        set((state) => {
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
        const currentTab = get().tabs[tabId];
        if (!currentTab) return;

        // 1. selective child tabs destruction
        // If we select a node that is NOT the source of an existing child tab, destroy that child tab
        currentTab.childrenIds.forEach((childId) => {
          const childTab = get().tabs[childId];
          if (childTab && childTab.sourceCallNodeId !== node?._key) {
            get().destroyTabBranch(childId);
          }
        });

        // 2. Update selection for the current tab in project store
        useProjectStore.getState().setSelectedNode(tabId, node);
        console.log("node", node);

        // 2. If it's a CallNode, create a new child tab (Portal)
        if (node && node.node_type === 'call') {
          // Check if parent has valid focus context (at least one node in focus stack)
          const parentFocusStack = useProjectStore.getState().focusStack[tabId];
          if (!parentFocusStack || parentFocusStack.length === 0) return;

          const callNode = node as any;
          const target = callNode.target;

          if (target) {
            // Check if we already have a tab for this specific call node
            const existingChildId = currentTab.childrenIds.find(id => get().tabs[id]?.sourceCallNodeId === node._key);
            if (existingChildId) return;

            const projectData = useProjectStore.getState().projectData;
            const lineage = findNodeLineage(projectData, target._key);

            const newTabId = crypto.randomUUID();
            const newTab: TabData = {
              id: newTabId,
              title: `Explore: ${target.name}`,
              parentId: tabId,
              sourceCallNodeId: node._key,
              childrenIds: [],
            };

            // Add the tab
            get().addTab(newTab);

            // Set selected node for the NEW tab
            useProjectStore.getState().setSelectedNode(newTabId, target);

            if (lineage && lineage.length > 0) {
              // Initialize focus stack with lineage
              useProjectStore.getState().pushFocusBulk(newTabId, lineage);

              // Auto-expand folders/files/nodes in the lineage including target
              const expandKeys = lineage.map((n: AnyNodeTree) => n._key);
              useProjectStore.getState().expandNodesBulk(newTabId, expandKeys);
            } else {
              // Fallback
              useProjectStore.getState().pushFocus(newTabId, target as any);
            }

            // Note: Auto-activation removed based on user request "it wont be active if the user did not click on it"
          }
        }
      },
    })),
    { name: 'tab-store' }
  )
);

export default useTabStore;
