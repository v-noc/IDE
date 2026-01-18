# Step 1: Tab State Slice Design (Refined)

## Goal
Create a `tabsSlice` to manage the hierarchical "portal" contexts.

## Concept
Tabs act as **Drill-Down Contexts**. All tabs view the same `projectData`, but each tab has its own `focusStack` (view depth) and `selection`.
-   **Root Tab**: Always exists.
-   **Child Tabs**: Created only when a `CallNode` is selected in the parent.
-   **Lifecycle**: Tied strictly to the parent's selection. If parent selection changes, the child tab is destroyed.

## State Structure

```typescript
// types/tabs.ts

export interface TabData {
  id: string; // UUID
  title: string; // e.g. "Function: process_data"
  parentId: string | null;
  /** 
   * The ID of the CallNode in the PARENT tab that spawned this tab.
   * Used to validate if this tab should still exist (i.e. does parent still select this node?).
   */
  sourceCallNodeId: string | null; 
  childrenIds: string[]; // Usually just 1 active child in this strict model, but array allows flexibility
}

export interface TabsSlice {
  tabs: Record<string, TabData>;
  rootTabId: string;
  activeTabId: string;

  // Actions
  addTab: (tab: TabData) => void;
  removeTab: (tabId: string) => void;
  setActiveTab: (tabId: string) => void;
  /**
   * Destroys the given tab and ALL its descendants.
   * Used when a parent tab changes selection.
   */
  destroyTabBranch: (tabId: string) => void; 
}
```

## Integration
- Store `tabs` in a normalized record.
- Initialize with one constant `ROOT` tab.
