# Step 3: Selectors (Refined)

## Goal
Selectors to visualize the "Drill-Down" path.

## Selectors

1.  **`useActiveTabId`**: Returns current active tab ID.
2.  **`useTabBreadcrumbs`**:
    *   Starting from `activeTabId`, walk up `parentId` safely to `ROOT`.
    *   Return array: `[RootTab, ChildTabA, ChildTabB]`.
    *   This is crucial for the UI header: `Main > Process User > Validate Email`.
3.  **`useTabState(tabId)`**:
    *   Returns `{ selectedNode, focusStack, ... }` for the specific tab.

## Interaction Selectors

*   **`useCurrentContext`**:
    *   Combines `activeTabId` with the resolved Project Data.
    *   If `focusStack[activeTabId]` has items, the "View Root" for the renderer is the top of that stack.
    *   Else, "View Root" is the global Project Root.
