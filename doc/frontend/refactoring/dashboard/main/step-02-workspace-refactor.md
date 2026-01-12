# Step 2: Central Workspace - Refactor (Container/Presenter)

## Goal
Architect the `Workspace` (formerly MainCanvas) using the Container/Presenter pattern to separate data fetching from layout rendering.

**Constraint:** NO FUNCTIONAL CHANGES.
**Pattern:** `WorkspaceContainer` (Data) -> `WorkspaceLayout` (UI).

---

## Current State

**File:** `features/Main/index.tsx` (278 lines)

### Issues
- Mixes store subscriptions (`useProjectStore`) with complex JSX layout.
- Mixes effect logic (tab syncing, document fetching) with rendering.

---

## Plan: Component Architecture

```
features/Main/
├── index.tsx                 # Exports WorkspaceContainer as default "Workspace"
├── components/
│   ├── WorkspaceLayout.tsx   # Pure UI: Grid/Tabs/Header layout
│   ├── WorkspaceHeader.tsx   # Pure UI: Breadcrumbs
│   ├── WorkspaceTabs.tsx     # Pure UI: Tab content area
│   └── ...
└── hooks/
    ├── useWorkspaceState.ts  # Data: Derived state (path, selection)
    └── useWorkspaceActions.ts # Actions: Promote, update doc
```

---

## Step 2a: Workspace Layout (Presenter)

### NEW: `features/Main/components/WorkspaceLayout.tsx`

Pure functional component. Receives all data as props.

```typescript
interface WorkspaceLayoutProps {
    // State
    isCodeActive: boolean;
    tabValue: string;
    displayPath: string;
    suffixName: string;
    // Actions
    onTabChange: (val: string) => void;
    onPromote: () => void;
    // Slots/Children (optional, or explicit components)
}

export function WorkspaceLayout({ 
  isCodeActive, tabValue, onTabChange, displayPath, suffixName, onPromote 
}: WorkspaceLayoutProps) {
  return (
    <div className="relative h-full w-full bg-[var(--background-color)]">
       <ResizablePanelGroup ...>
          <WorkspaceTabs 
             activeTab={tabValue}
             onTabChange={onTabChange}
             header={
                <WorkspaceHeader 
                   displayPath={displayPath} 
                   suffixName={suffixName}
                   onPromote={onPromote} 
                />
             }
          />
          {/* ... */}
       </ResizablePanelGroup>
    </div>
  );
}
```

---

## Step 2b: Workspace Header (Pure)

### NEW: `features/Main/components/WorkspaceHeader.tsx`

Strictly presentational. No store imports.

```typescript
export function WorkspaceHeader({ displayPath, suffixName, onPromote }) {
  return (
    <div className="px-2 text-xs text-muted-foreground truncate">
       {displayPath || "No selection"}
       {suffixName && (
         <button onClick={onPromote}>(promote)</button>
       )}
    </div>
  );
}
```

---

## Step 2c: Container (Logic)

### MODIFY: `features/Main/index.tsx`

Handles all the hooks and state.

```typescript
import { WorkspaceLayout } from './components/WorkspaceLayout';

const Workspace = () => {
   // 1. Hooks (Logic)
   const { selectedNode, secondarySelectedNode } = useProjectStore();
   const { suffixName, displayPath } = useWorkspaceState(selectedNode, secondarySelectedNode);
   
   // 2. Handlers
   const handlePromote = useCallback(() => { ... }, []);

   // 3. Render Presenter
   return (
     <WorkspaceLayout 
        displayPath={displayPath}
        suffixName={suffixName}
        onPromote={handlePromote}
        // ...
     />
   );
};

export default Workspace;
```

---

## Verification

- [ ] Presentational components have 0 dependencies on Stores/Hooks.
- [ ] Logic is isolated in the Container or Custom Hooks.
- [ ] No visual regression.

---

## Next Step
🎉 Review and Execute.
