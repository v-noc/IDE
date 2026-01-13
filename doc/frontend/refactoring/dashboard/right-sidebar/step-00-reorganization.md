# Step 0: Right Sidebar - Reorganization

## Goal
Move the Right Sidebar from a nested component inside `Main` to a top-level feature under `Dashboard`.

**Constraint:** NO FUNCTIONAL CHANGES. This is purely a file system move to improve architectural clarity.

---

## Current State

**Location:** `src/frontend/src/features/Dashboard/features/Main/components/RightSidebar`

### Issues
1. **Nesting Depth:** It is nested 6 levels deep (`Dashboard/features/Main/components/RightSidebar`), making imports long and fragile.
2. **Architectural Mismatch:** The `LeftSidebar` is a top-level feature (`features/Sidebar`), while `RightSidebar` is treated as a child of `Main`.
3. **Detached Feeling:** As noted by the user, it feels "detached" from the rest of the dashboard structure.

---

## Step 0a: Create New Folder Structure

We will create a new directory `src/frontend/src/features/Dashboard/features/RightSidebar`.

```
src/frontend/src/features/Dashboard/features/
├── Main/                  # Existing
├── Sidebar/               # Existing (Left Sidebar)
└── RightSidebar/          # NEW
    ├── components/        # Moves here
    ├── hooks/             # Moves here
    ├── index.tsx          # Moves here
    ├── BaseClass.tsx      # Moves here
    └── CallSidebar.tsx    # Moves here
```

---

## Step 0b: Move Files

Command sequence (for reference):
```bash
mv src/frontend/src/features/Dashboard/features/Main/components/RightSidebar src/frontend/src/features/Dashboard/features/RightSidebar
```

---

## Step 0c: Update Imports in `MainWithRightSidebar.tsx`

**File:** `src/frontend/src/features/Dashboard/features/Main/MainWithRightSidebar.tsx`

### Before
```typescript
import { RightSidebar } from "./components/RightSidebar";
```

### After
```typescript
import { RightSidebar } from "../RightSidebar";
```

---

## Verification Plan

### 1. File System Check
- Verify `features/Main/components/RightSidebar` no longer exists.
- Verify `features/RightSidebar` exists and contains `index.tsx`.

### 2. Compilation Check
- Run `tsc` (or wait for IDE feedback) to ensure no broken imports.

### 3. Runtime Check
- Open Dashboard.
- Verify Right Sidebar appears on the right side.
- Verify toggle button still works.

---

## Next Step
👉 [step-01-split-handlers.md](./step-01-split-handlers.md)
