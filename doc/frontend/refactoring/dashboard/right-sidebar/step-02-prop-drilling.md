# Step 2: Right Sidebar - Prop Drilling (Simplified)

## Goal
Simplify the prop passing to `ConfigSidebarContent` by leveraging the strict hook separation from Step 1.

**Constraint:** NO FUNCTIONAL CHANGES.

---

## Current State

**File:** `RightSidebar/index.tsx`

Previously, we planned to extract a complex `useSidebarProps` hook. However, with the new `useRightSidebarState` and `useRightSidebarHandlers` from Step 1, the main component becomes a simple composer.

---

## Plan: Composition

The `RightSidebar` component (the inner content part, let's call it `RightSidebarContent` to be safe/clear in the plan) will simply compose the hooks.

```typescript
// RIGHT SIDEBAR CONTENT (Inside the layout)

export const RightSidebarContent = () => {
  // 1. Get State
  const { initialBasicInfo, initialCustomization } = useRightSidebarState();
  
  // 2. Get Handlers
  const { handleThemeChange, handleBasicInfoChange } = useRightSidebarHandlers();

  // 3. Render
  return (
      <ConfigSidebarContent 
        initialBasicInfo={initialBasicInfo}
        initialCustomization={initialCustomization}
        onChangeBasicInfo={handleBasicInfoChange}
        onChangeCustomization={handleThemeChange}
      />
  );
};
```

**Outcome:** We don't need a dedicated `useSidebarProps` hook anymore because the state and handlers are already separated and ready to be passed directly. This implies `step-02-prop-drilling.md` is effectively "Verify Composition" or "Create Wrapper".

---

## Step 2a: Update `ConfigSidebarContent` (Interface Check)

Ensure `ConfigSidebarContent` (renamed or imported from `SidebarTabs.tsx`) accepts these explicit props. It currently expects `...sidebarProps`.

We will ensure the interface aligns with the output of our hooks.

---

## Verification

- [ ] Verify `ConfigSidebarContent` receives the exact same data structure.
- [ ] Verify no unnecessary re-renders (hooks are memoized).

---

## Next Step
👉 [step-03-component-split.md](./step-03-component-split.md)
