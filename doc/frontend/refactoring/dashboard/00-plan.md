# Dashboard Component Refactoring Plan

## Overview

Step-by-step refactoring guide for Dashboard components, organized by visual layout.

```
┌─────────────────────────────────────────────────────────────────┐
│                          Navbar                                 │
├─────────────┬───────────────────────────────┬───────────────────┤
│             │                               │                   │
│   Left      │           Main                │    Right          │
│  Sidebar    │                               │   Sidebar         │
│             │   ┌───────────────────────┐   │ ┌───────────────┐ │
│  - Project  │   │      Canvas/Code      │   │ │  Top: Config  │ │
│    Tree     │   │                       │   │ ├───────────────┤ │
│             │   └───────────────────────┘   │ │ Bottom: Tabs  │ │
│             │                               │ │ (Calls/Base)  │ │
│             │                               │ └───────────────┘ │
└─────────────┴───────────────────────────────┴───────────────────┘
```

---

## Refactoring Steps

| Step | Component | Goal | Time |
|------|-----------|------|------|
| [1](./layout/step-01-layout-cleanup.md) | `Layout.tsx` | Extract theme logic | 30 min |
| [2](./layout/step-02-layout-composition.md) | `Layout.tsx` | Slot-based design | 25 min |
| [3](./left-sidebar/step-01-sidebar-cleanup.md) | `SideBar.tsx` | Extract tree logic | 30 min |
| [4](./left-sidebar/step-02-tree-node.md) | `TreeNode/` | Memoization | 20 min |
| [5](./main/step-01-main-cleanup.md) | `Main/` | Clean up index | 20 min |
| [6](./right-sidebar/step-01-split-handlers.md) | `RightSidebar/` | Extract handlers | 30 min |
| [7](./right-sidebar/step-02-top-section.md) | `RightSidebar/` | Config section | 20 min |
| [8](./right-sidebar/step-03-bottom-section.md) | `RightSidebar/` | Tabs section | 20 min |

---

## Current Files

| File | Lines | Issues |
|------|-------|--------|
| `pages/Dashboard.tsx` | 169 | Utility functions mixed in, socket init logic |
| `components/Layout.tsx` | 231 | Theme logic embedded, too many responsibilities |
| `Main/MainWithRightSidebar.tsx` | 71 | Good, minor cleanup |
| `RightSidebar/index.tsx` | 245 | Update handlers embedded, tree mutation logic |
| `Sidebar/components/SideBar.tsx` | ~170 | Mixed concerns |

---

## Start Here

👉 [Step 1: Layout Cleanup](./layout/step-01-layout-cleanup.md)
