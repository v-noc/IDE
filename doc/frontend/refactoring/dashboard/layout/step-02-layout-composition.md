# Step 2: Layout - Slot-Based Composition

## Goal
Refactor Layout to use a cleaner slot-based pattern.

## Why
Currently Layout receives children as separate props:
```typescript
<Layout
  main={<MainWithRightSidebar left={<MainCanvas />} />}
  navbar={<Navbar />}
  leftSidebar={<SideBar />}
/>
```

The panel logic is embedded in Layout. A cleaner approach separates concerns.

---

## Simplified Layout

After Step 1, Layout should look like this:

### Updated: `features/Dashboard/components/Layout.tsx`

```typescript
import { ResizableHandle, ResizablePanel } from "@/components/ui/resizable";
import { useState, useRef, useEffect, ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ImperativePanelHandle } from "react-resizable-panels";
import { useResolvedTheme } from "../hooks/useResolvedTheme";

interface LayoutProps {
  navbar: ReactNode;
  leftSidebar: ReactNode;
  main: ReactNode;
  rightSidebar?: ReactNode;
  defaultLeftOpen?: boolean;
}

const Layout = ({
  main,
  navbar,
  leftSidebar,
  rightSidebar,
  defaultLeftOpen = true,
}: LayoutProps) => {
  const [isLeftOpen, setIsLeftOpen] = useState(defaultLeftOpen);
  const leftPanelRef = useRef<ImperativePanelHandle>(null);
  const { themeStyles } = useResolvedTheme();

  // Sync panel state
  useEffect(() => {
    const panel = leftPanelRef.current;
    if (!panel) return;
    if (isLeftOpen && panel.isCollapsed()) {
      panel.expand();
    } else if (!isLeftOpen && !panel.isCollapsed()) {
      panel.collapse();
    }
  }, [isLeftOpen]);

  return (
    <div className="relative flex min-h-screen max-h-screen w-full h-full" style={themeStyles}>
      {/* Left Sidebar */}
      <ResizablePanel
        ref={leftPanelRef}
        defaultSize={20}
        collapsible
        collapsedSize={0}
        minSize={12}
        className="relative bg-[var(--left-sidebar-color)] group"
      >
        <CollapseButton
          side="left"
          onClick={() => setIsLeftOpen(false)}
        />
        {leftSidebar}
      </ResizablePanel>

      <ResizableHandle className="w-px border-l-2 hover:border-border hover:bg-border/20 transition-colors" />

      {/* Expand button when collapsed */}
      {!isLeftOpen && (
        <ExpandButton side="left" onClick={() => setIsLeftOpen(true)} />
      )}

      {/* Main Content */}
      <ResizablePanel
        defaultSize={80}
        className="flex-1 flex flex-col w-full bg-[var(--background-color)]"
      >
        <nav className="border-b shadow-sidebar bg-[var(--navbar-color)]">
          {navbar}
        </nav>
        <main className="flex-1 min-h-0 h-full">
          {main}
        </main>
      </ResizablePanel>
    </div>
  );
};

// Small extracted components
function CollapseButton({ side, onClick }: { side: 'left' | 'right'; onClick: () => void }) {
  const Icon = side === 'left' ? ChevronLeft : ChevronRight;
  const position = side === 'left' ? '-right-3' : '-left-3';
  
  return (
    <button
      type="button"
      aria-label={`Close ${side} sidebar`}
      onClick={onClick}
      className={`absolute ${position} top-1/2 z-50 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity`}
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

function ExpandButton({ side, onClick }: { side: 'left' | 'right'; onClick: () => void }) {
  const Icon = side === 'left' ? ChevronRight : ChevronLeft;
  const position = side === 'left' ? 'left-0' : 'right-0';
  
  return (
    <button
      type="button"
      aria-label={`Open ${side} sidebar`}
      onClick={onClick}
      className={`absolute ${position} top-1/2 -translate-y-1/2 z-50 p-1 py-2 bg-white border rounded-md shadow hover:bg-gray-50`}
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

export default Layout;
```

---

## Optional: Extract Panel Hook

### NEW: `features/Dashboard/hooks/useCollapsiblePanel.ts`

```typescript
import { useRef, useState, useEffect } from 'react';
import type { ImperativePanelHandle } from 'react-resizable-panels';

export function useCollapsiblePanel(defaultOpen = true) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const panelRef = useRef<ImperativePanelHandle>(null);

  useEffect(() => {
    const panel = panelRef.current;
    if (!panel) return;
    
    if (isOpen && panel.isCollapsed()) {
      panel.expand();
    } else if (!isOpen && !panel.isCollapsed()) {
      panel.collapse();
    }
  }, [isOpen]);

  return {
    panelRef,
    isOpen,
    toggle: () => setIsOpen((prev) => !prev),
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
  };
}
```

Usage:
```typescript
const leftPanel = useCollapsiblePanel(true);

<ResizablePanel ref={leftPanel.panelRef} ... >
  <CollapseButton onClick={leftPanel.close} />
  {leftSidebar}
</ResizablePanel>

{!leftPanel.isOpen && <ExpandButton onClick={leftPanel.open} />}
```

---

## Verification

- [ ] Left sidebar still collapses/expands
- [ ] Theme still applies
- [ ] Layout.tsx is now cleaner (~80-100 lines)

---

## Next Step

👉 [../left-sidebar/step-01-sidebar-cleanup.md](../left-sidebar/step-01-sidebar-cleanup.md)
