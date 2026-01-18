# Step 5: Sidebar UI/UX Design

## Goal
Design a "Context Stack" Sidebar that visualizes the drill-down path while maintaining clarity and usability.

## Structure

The Sidebar replaces its single static `ProjectTree` with a dynamic **Vertical Stack** of contexts.

### Component Composition

```tsx
<SidebarContainer>
  <SidebarHeader /> {/* Global Search/Filter */}
  
  <ResizablePanelGroup direction="vertical">
      
      {/* 1. Root Context (Always Present) */}
      <ContextPanel 
          tab={rootTab} 
          isActive={activeTabId === rootTab.id} 
      />

      {/* 2. Drilled Contexts (Dynamic) */}
      {childTabs.map((tab) => (
          <>
            <ResizableHandle />
            <ContextPanel 
                key={tab.id}
                tab={tab}
                isActive={activeTabId === tab.id}
            />
          </>
      ))}

  </ResizablePanelGroup>
  
  <SidebarDialogs />
</SidebarContainer>
```

## Component: `ContextPanel`

This is the wrapper for each "level" of the stack.

*   **Header**:
    *   **Icon**: `FolderTree` (Root) vs `Function/Call` icon (Drilled).
    *   **Title**: "Project Root" vs "func: process_data".
    *   **Badges**: Show "Read-only" or "Focus" state if applicable.
    *   **Controls**:
        *   **Collapse/Expand**: Keep the panel but minimize content height.
        *   **Close (X)**: *Only for child panels.* Destroys this context (pops the stack).
*   **Body**:
    *   Renders `ProjectTree` with `tabId` prop.
    *   The tree automatically scopes itself via the `focusStack` of that tab.

## UX/Visual Suggestions

### 1. Visual Depth (The "Stack" Effect)
To make it feel like user is going "deeper":
*   **Indentation**: Maybe slight left-border width increase for deeper panels?
*   **Background**:
    *   Root: `bg-sidebar`
    *   Level 1: `bg-sidebar-accent/5` (Slightly lighter/darker)
    *   Level 2: `bg-sidebar-accent/10`
*   **Shadows**: Drop shadow from the *bottom* of the upper panel onto the lower panel to suggest stacking order.

### 2. Active State Indicators
The user can click any panel to "activate" that context (switch the Main Workspace view).
*   **Inactive Panel**:
    *   Opacity: 70%.
    *   Border: Transparent.
*   **Active Panel**:
    *   Opacity: 100%.
    *   Border: **Left Border Highlight** (primary color, 2px).
    *   Header Text: Primary Color.

### 3. Transitions
*   **Entry**: When a new tab is created (user clicks a call), the new panel should **Slide Down** and **Fade In** at the bottom.
*   **Auto-Scroll**: The Sidebar should scroll to reveal the new panel title automatically.

### 4. Resizability
*   Valid concern: Too many levels = tiny panels.
*   **Logic**:
    *   **Auto-Collapse**: If stack size > 2, automatically collapse the Root panel to just its Header?
    *   **Min-Height**: Enforce reasonable min-height (e.g., 200px) or allow scroll within the sidebar container itself if panels overflow.

## Proposed Code Structure for `ContextPanel.tsx`

```tsx
export const ContextPanel = ({ tab, isActive, onClick }: ContextPanelProps) => {
  return (
    <ResizablePanel onClick={onClick} className={cn("flex flex-col", isActive ? "bg-background" : "bg-muted/20")}>
      
      {/* Header */}
      <div className={cn("flex items-center p-2 border-b select-none cursor-pointer", isActive && "border-primary/20 bg-primary/5")}>
         <Icon className="mr-2 size-4" />
         <span className="font-medium text-xs">{tab.title}</span>
         <div className="ml-auto flex gap-1">
            {/* Action Buttons */}
         </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
         <ProjectTree tabId={tab.id} />
      </div>

    </ResizablePanel>
  )
}
```
