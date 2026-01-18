# Step 4: UI Integration (Vertical Sidebar + Context-Aware Workspace)

## Goal
Combine vertical Sidebar drill-down with a Context-Aware Main Workspace.

## 1. Sidebar: Vertical Stack (Navigation)
*   **Component**: `SideBar.tsx`
*   **Behavior**: Renders a vertical stack of panels corresponding to the `tabStack` (lineage of the active tab).
*   **Interaction**: clicking a panel activates that tab (sets `activeTabId`).

## 2. Main Workspace: Context-Aware Rendering
*   **Component**: `Dashboard.tsx`
*   **Concept**: The Main Layout does NOT use a visual Tab bar. It simply acts as a container that displays the content relative to the **Active Tab**.
*   **Mechanism**: Pass `activeTabId` to the `Workspace` component.

### Implementation

### Implementation

In `Dashboard.tsx`:

```tsx
const { activeTabId, tabStack } = useTabSelectors();

// Render ALL valid tabs to preserve DOM state
// Use CSS to hide inactive ones
return (
  <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <RightSidebar>
             {/* Iterate over the active stack (active branch) */}
             {/* Since we only support a single active branch, this covers all relevant open tabs */}
             {tabStack.map((tab) => (
                <div 
                  key={tab.id} 
                  className={cn("h-full w-full", tab.id !== activeTabId && "hidden")}
                >
                    <Workspace tabId={tab.id} />
                </div>
             ))}
          </RightSidebar>
        }
        // ...
      />
  </ResizablePanelGroup>
);
```

### 3. Workspace Component Update
*   **File**: `src/frontend/src/features/Dashboard/features/Main/index.tsx`
*   **Change**: Update `Workspace` to accept `tabId` prop.
*   **Logic**: 
    *   Use `useProjectStore(s => s.selectedNode[tabId])` 
    *   Use `useProjectStore(s => s.focusedNode[tabId])`
    *   This ensures that when `Dashboard` switches `activeTabId`, the entire Workspace re-renders with the new context (focus stack, selection, open docs) effectively acting as a "Portal".

## Visuals
*   **Sidebar**: "Stack of cards" showing the depth.
*   **Main**: Just the content. The "Context Switch" happens instantly when clicking sidebar panels or drilling down.
