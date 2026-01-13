# Step 0: Right Sidebar - Layout Merge

## Goal
Merge `MainWithRightSidebar.tsx` into `RightSidebar/index.tsx` to unify the layout logic and content.

**Constraint:** NO FUNCTIONAL CHANGES. The layout behavior (`ResizablePanelGroup`, toggling) must remain identical.
**Constraint:** DO NOT Move folders. Keep `RightSidebar` in `src/frontend/src/features/Dashboard/features/Main/components/RightSidebar`.

---

## Current State

Two components manage the Right Sidebar:
1. **`MainWithRightSidebar.tsx`**: Wrapper. Manages `ResizablePanelGroup`, `open` state, and the Toggle Button.
2. **`RightSidebar/index.tsx`**: Content. Manages the internal layout (Top/Bottom panels) and form logic.

This separation is confusing and creates a "detached" feeling.

---

## Plan: Unify to `RightSidebarLayout`

We will modify `RightSidebar/index.tsx` to accept `children` (the workspace) and handle the outer layout itself.

### 1. Update `RightSidebar/index.tsx`

It will look roughly like this (pseudo-code):

```typescript
// features/Main/components/RightSidebar/index.tsx

interface RightSidebarProps {
  children?: React.ReactNode; // NEW: The workspace content
  className?: string; // Kept for compatibility if used
  // onToggle removed? No, managed internally now.
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ children, className }) => {
  // State from MainWithRightSidebar
  const [isOpen, setIsOpen] = useState(true);

  // Existing hooks from RightSidebar
  const { ... } = useNodeUpdates();

  return (
    <div className="relative h-full w-full min-h-0 overflow-hidden">
       {/* Outer Resizable Group (from MainWithRightSidebar) */}
       <ResizablePanelGroup direction="horizontal">
          
          {/* LEFT PANEL (Workspace) */}
          <ResizablePanel defaultSize={isOpen ? 75 : 100} minSize={40}>
            {children}
          </ResizablePanel>

          {/* RIGHT PANEL (Sidebar) */}
          {isOpen && (
             <>
               <ResizableHandle />
               <ResizablePanel defaultSize={25} minSize={15}>
                  {/* EXISTING RIGHT SIDEBAR CONTENT */}
                  <aside className="...">
                     <ResizablePanelGroup direction="vertical">
                        {/* Top Config */}
                        {/* Bottom Tabs */}
                     </ResizablePanelGroup>
                  </aside>
               </ResizablePanel>
             </>
          )}

       </ResizablePanelGroup>

       {/* Toggle Button Logic (from MainWithRightSidebar) */}
       {!isOpen && (
         <button onClick={() => setIsOpen(true)}>Open</button>
       )}
    </div>
  );
}
```

### 2. Update `Dashboard.tsx` (or parent)

**Before:**
```typescript
<Layout
  main={<MainWithRightSidebar left={<MainCanvas />} />}
  ...
/>
```

**After:**
```typescript
import { RightSidebar } from './features/Main/components/RightSidebar';

<Layout
  main={
    <RightSidebar>
      <MainCanvas />
    </RightSidebar>
  }
  ...
/>
```

### 3. Delete `MainWithRightSidebar.tsx`

---

## Verification

### 1. Layout Integrity
- Verify the `ResizablePanelGroup` correctly wraps both the workspace and sidebar.
- Verify the toggle button (Chevron) works to open/close.

### 2. Sizing
- Verify default sizes (75/25) are preserved.

---

## Next Step
👉 [step-01-split-handlers.md](./step-01-split-handlers.md)
