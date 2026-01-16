import type { TabData } from '@/types/tabs';
import type { TabStore } from '../useTabStore';

/**
 * Returns the stack of tabs from the root to the active tab ID.
 */
export const selectTabStack = (state: TabStore): TabData[] => {
    const stack: TabData[] = [];

    const traverse = (id: string) => {
        const tab = state.tabs[id];
        if (!tab) return;
        stack.push(tab);
        if (tab.childrenIds) {
            tab.childrenIds.forEach(traverse);
        }
    };

    traverse(state.rootTabId);
    return stack;
};

/**
 * Returns the lineage for a specific tab ID.
 */
export const selectTabLineage = (state: TabStore, tabId: string): TabData[] => {
    const stack: TabData[] = [];
    let currentId: string | null = tabId;

    while (currentId && state.tabs[currentId]) {
        const tab: TabData = state.tabs[currentId];
        stack.unshift(tab);
        currentId = tab.parentId;
    }

    return stack;
};

export const selectActiveTab = (state: TabStore): TabData | undefined => {
    return state.tabs[state.activeTabId];
};
