# Step 3: Right Sidebar - Bottom Section (Tabs)

## Goal
Extract the bottom tabs section into its own component.

---

## Current State

```typescript
// In RightSidebar/index.tsx (lines 210-238)
<ResizablePanel collapsible defaultSize={35} minSize={20}>
  <div className="h-full min-h-0 flex flex-col">
    <Tabs defaultValue="calls" className="flex-1 min-h-0 flex flex-col">
      <TabsList className="...">
        <TabsTrigger value="calls">Calls</TabsTrigger>
        <TabsTrigger value="base">Base Class</TabsTrigger>
      </TabsList>
      <TabsContent value="calls" className="flex-1 min-h-0">
        <CallSidebar hideHeader />
      </TabsContent>
      <TabsContent value="base" className="flex-1 min-h-0 overflow-auto">
        <BaseClass />
      </TabsContent>
    </Tabs>
  </div>
</ResizablePanel>
```

---

## Extract: `RightSidebar/components/BottomTabs.tsx`

```typescript
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import CallSidebar from '../CallSidebar';
import BaseClass from '../BaseClass';

export function BottomTabs() {
  return (
    <div className="h-full min-h-0 flex flex-col">
      <Tabs defaultValue="calls" className="flex-1 min-h-0 flex flex-col">
        <TabsList className="w-full p-0 bg-[var(--right-sidebar-color)]">
          <TabsTrigger
            className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
            value="calls"
          >
            Calls
          </TabsTrigger>
          <TabsTrigger
            className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
            value="base"
          >
            Base Class
          </TabsTrigger>
        </TabsList>

        <TabsContent value="calls" className="flex-1 min-h-0">
          <CallSidebar hideHeader />
        </TabsContent>

        <TabsContent value="base" className="flex-1 min-h-0 overflow-auto px-3 py-2">
          <BaseClass />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

## Final RightSidebar Structure

```
RightSidebar/
├── index.tsx                 # Main (~50 lines)
├── BaseClass.tsx
├── CallSidebar.tsx
├── components/
│   ├── SidebarTabs.tsx       # Top config content
│   ├── BottomTabs.tsx        # NEW: Bottom tabs
│   └── sections/
│       ├── BasicInfoSection.tsx
│       ├── CustomizationSection.tsx
│       ├── DocumentsList.tsx
│       ├── LogsSection.tsx
│       └── ...
└── hooks/
    ├── useNodeUpdates.ts     # NEW: Update handlers
    ├── useSidebarProps.ts    # NEW: Props builder
    └── useConfigSidebarForm.ts
```

---

## Verification

- [ ] Tabs still switch correctly
- [ ] Calls sidebar still shows calls
- [ ] Base class still renders

---

## 🎉 Dashboard Refactoring Complete!

You've completed all dashboard component refactoring steps:

| Area | What was done |
|------|---------------|
| Layout | Extracted theme hook, simplified to ~100 lines |
| Left Sidebar | Extracted tree filter, memoized TreeNode |
| Main | Moved utilities to `treeUtils.ts` |
| Right Sidebar | Extracted handlers, split into components |

---

## Combined With Previous Steps

If you've also done the [previous refactoring](../00-plan.md), you now have:

✅ Centralized query keys  
✅ Unified code/logs services  
✅ Socket React Context  
✅ Socket → React Query sync  
✅ Clean Canvas components  
✅ Optimized performance  
✅ Store slices  
✅ Clean Layout  
✅ Clean Sidebars
