# Step 2: Tab Logic & Middleware (Refined)

## Goal
Implement the strict "Portal" logic: Selecting a `CallNode` opens a portal (Child Tab); deselecting closes it.

## The "Handle Selection" Logic

This logic replaces the standard `setSelectedNode`.

**Action**: `handleNodeSelection(tabId: string, node: AnyNodeTree | null)`

### Flow

1.  **Update Selection**:
    *   Set `selectedNode[tabId] = node`.

2.  **Cleanup Children**:
    *   Check `tabs[tabId].childrenIds`.
    *   **Crucial Step**: Since the selection has changed (or might have), the *reason* for any existing child tabs (the previous selection) is gone.
    *   **Action**: Recursively destroy **ALL** children of `tabId`.
        *   (Optimization: If `node` is the *same* CallNode as before, we might preserve the child, but "Destroy & Recreate" ensures clean state as requested).

3.  **Create New Context (If Applicable)**:
    *   **Check**: Is `node` a `CallNode`?
    *   **If Yes**:
        1.  **Resolve Target**: Find the `target_function` or file referenced by the call.
        2.  **Create Tab**:
            *   Generate `newTabId`.
            *   Create `TabData`: `{ id: newTabId, parentId: tabId, sourceCallNodeId: node.id, ... }`.
            *   Update `tabs` state.
        3.  **Initialize Tab State**:
            *   **Focus**: Use `focusSlice` to push the `target_function` (or relevant node) onto the `focusStack` of `newTabId`.
            *   **Selection**: Clear selection for `newTabId`.
        4.  **Auto-Switch**:
            *   Set `activeTabId = newTabId`. (Or keep parent active? User said "we just create onther child tab where they can go exploere", implying navigation to it).

## Scenarios

*   **User clicks regular File Node**: 
    *   Selects node.
    *   Destroys any existing child tabs (closing the portal).
*   **User clicks Call Node**:
    *   Selects node.
    *   Destroys old children.
    *   Creates new Child Tab focused on the call target.
    *   Switches view to Child Tab.
