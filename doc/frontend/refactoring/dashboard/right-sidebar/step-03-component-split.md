# Step 3: Right Sidebar - Component Split

## Goal
Extract the bottom tabs section into a pure presentational component.

**Constraint:** NO FUNCTIONAL CHANGES.

---

## Current State

**File:** `RightSidebar/index.tsx` (Lines 210-238) contains the JSX for the Tabs logic.

---

## Plan: Presentational Component

### NEW: `RightSidebar/components/RightSidebarTabs.tsx`

(Renamed from `BottomTabs` to be more explicit about where it belongs).

```typescript
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import CallSidebar from '../CallSidebar';
import BaseClass from '../BaseClass';

interface RightSidebarTabsProps {
  // Add props if we need to control tab state from outside
  // For now, it seems self-contained or uncontrolled
  className?: string;
}

export function RightSidebarTabs({ className }: RightSidebarTabsProps) {
  return (
    <div className={`h-full min-h-0 flex flex-col ${className}`}>
      <Tabs defaultValue="calls" className="flex-1 min-h-0 flex flex-col">
        {/* ... Tab List ... */}
        {/* ... Tab Content ... */}
      </Tabs>
    </div>
  );
}
```

---

## Layout Composition (Main Component)

After Step 0, 1, 2, and 3, `RightSidebar/index.tsx` becomes:

```typescript
export const RightSidebar = ({ children }) => { // The merged layout wrapper
  const [isOpen, setIsOpen] = useState(true);

  // Hook calls for sidebar content
  const { initialBasicInfo, initialCustomization } = useRightSidebarState();
  const { handleThemeChange, handleBasicInfoChange } = useRightSidebarHandlers();

  return (
     <ResizablePanelGroup ...>
        <ResizablePanel ...>{children}</ResizablePanel>

        {isOpen && (
          <ResizablePanel ...> 
             <aside ...>
                <ResizablePanelGroup direction="vertical">
                   {/* Top: Config */}
                   <ConfigSidebarContent 
                      initialBasicInfo={initialBasicInfo}
                      ...
                   />

                   {/* Bottom: Tabs */}
                   <RightSidebarTabs />
                </ResizablePanelGroup>
             </aside>
          </ResizablePanel>
        )}
     </ResizablePanelGroup>
  );
}
```

---

## Verification

- [ ] Tabs render correctly.
- [ ] No layout regression.

---

## Next Step
👉 [../main/step-02-workspace-refactor.md](../main/step-02-workspace-refactor.md)
