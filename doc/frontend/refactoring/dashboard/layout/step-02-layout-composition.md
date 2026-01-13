# Step 2: Layout - Panel State & Composition (React 19)

## Goal
Create a reusable panel state hook and clean up Layout with slot composition.

---

## Pattern: Hook-Based Logic Separation

Extract panel logic into a reusable hook. This keeps JSX clean and logic testable.

---

## NEW: `features/Dashboard/hooks/usePanelState.ts`

```typescript
import { useState, useRef, useCallback } from 'react';
import type { ImperativePanelHandle } from 'react-resizable-panels';

export function usePanelState(defaultOpen = true) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const ref = useRef<ImperativePanelHandle>(null);

  const toggle = useCallback(() => {
    const panel = ref.current;
    if (!panel) return;
    
    if (isOpen) {
      panel.collapse();
    } else {
      panel.expand();
    }
    setIsOpen(!isOpen);
  }, [isOpen]);

  const open = useCallback(() => {
    const panel = ref.current;
    if (panel && !isOpen) {
      panel.expand();
      setIsOpen(true);
    }
  }, [isOpen]);

  const close = useCallback(() => {
    const panel = ref.current;
    if (panel && isOpen) {
      panel.collapse();
      setIsOpen(false);
    }
  }, [isOpen]);

  return { 
    isOpen, 
    toggle, 
    open, 
    close, 
    ref,
    // Handlers for ResizablePanel events
    onCollapse: () => setIsOpen(false),
    onExpand: () => setIsOpen(true),
  };
}
```

---

## Updated: `features/Dashboard/components/Layout.tsx`

```typescript
import { ReactNode } from 'react';
import { 
  ResizableHandle, 
  ResizablePanel, 
  ResizablePanelGroup 
} from '@/components/ui/resizable';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useResolvedTheme } from '../hooks/useResolvedTheme';
import { usePanelState } from '../hooks/usePanelState';

interface LayoutProps {
  navbar: ReactNode;
  leftSidebar: ReactNode;
  main: ReactNode;
}

export default function Layout({ navbar, leftSidebar, main }: LayoutProps) {
  // Theme - pure derived state
  const { cssVariables } = useResolvedTheme();
  
  // Panel state - encapsulated logic
  const leftPanel = usePanelState(true);

  return (
    <div 
      className="flex h-screen w-full flex-col overflow-hidden transition-colors duration-300"
      style={cssVariables}
    >
      <ResizablePanelGroup direction="horizontal">
        
        {/* Left Sidebar Slot */}
        <ResizablePanel
          ref={leftPanel.ref}
          defaultSize={20}
          collapsible
          collapsedSize={0}
          minSize={15}
          maxSize={30}
          onCollapse={leftPanel.onCollapse}
          onExpand={leftPanel.onExpand}
          className="relative border-r bg-[var(--left-sidebar-color)] transition-colors"
        >
          {/* Collapse trigger */}
          <button
            onClick={leftPanel.close}
            aria-label="Collapse sidebar"
            className="absolute right-2 top-2 z-10 rounded-full p-1.5 opacity-0 hover:bg-black/10 group-hover:opacity-100 transition-opacity"
          >
            <ChevronLeft size={16} />
          </button>
          
          {leftSidebar}
        </ResizablePanel>

        <ResizableHandle className="w-px hover:bg-border/50 transition-colors" />

        {/* Main Content */}
        <ResizablePanel defaultSize={80} className="flex flex-col">
          {/* Navbar Slot */}
          <nav className="border-b bg-[var(--navbar-color)] transition-colors">
            {navbar}
          </nav>

          {/* Main Content Slot */}
          <main className="flex-1 min-h-0 relative overflow-hidden">
            {/* Expand trigger (when collapsed) */}
            {!leftPanel.isOpen && (
              <button
                onClick={leftPanel.open}
                aria-label="Expand sidebar"
                className="absolute left-4 top-4 z-50 rounded-lg bg-white p-2 shadow-md hover:bg-gray-50"
              >
                <ChevronRight size={16} />
              </button>
            )}
            
            {main}
          </main>
        </ResizablePanel>

      </ResizablePanelGroup>
    </div>
  );
}
```

---

## Why This Is React 19 Ready

| Aspect | Benefit |
|--------|---------|
| **No useEffect** | Theme is derived, not synced |
| **Slot Pattern** | Parent controls what, Layout controls where |
| **Server Components Ready** | Layout = Client, slots can be Server |
| **CSS Variables** | Browser handles repaint, fewer re-renders |
| **Hook Separation** | Logic testable, JSX clean |
| **React Compiler Ready** | Can remove useMemo when compiler enabled |

---

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Layout.tsx lines | 231 | ~80 |
| useEffect calls | 2 | 0 |
| Responsibilities | 5+ | 2 (theme + panels) |
| Testable hooks | 0 | 2 |

---

## Verification

- [ ] Sidebar collapses/expands
- [ ] Theme applies correctly
- [ ] No useEffect warnings
- [ ] Layout.tsx is ~80 lines

---

## Next Step

👉 [../left-sidebar/step-01-sidebar-cleanup.md](../left-sidebar/step-01-sidebar-cleanup.md)
