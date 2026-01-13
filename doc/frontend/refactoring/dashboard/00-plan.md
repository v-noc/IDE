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
| [3](./left-sidebar/step-01-sidebar-cleanup.md) | `SideBar.tsx` | Modal store pattern | 30 min |
| [4](./left-sidebar/step-02-tree-node.md) | `TreeNode/` | Pure presentation + actions | 25 min |
| [5](./left-sidebar/step-03-project-tree.md) | `ProjectTree.tsx` | Extract utilities | 20 min |
| [6](./left-sidebar/step-04-node-content.md) | `NodeContent.tsx` | Split into pieces | 30 min |
| [7](./left-sidebar/step-05-use-tree-node.md) | `useTreeNode.ts` | Split into 3 hooks | 25 min |
| [8](./left-sidebar/step-06-context-menu.md) | `NodeContextMenu.tsx` | Single onAction prop | 15 min |
| [9](./main/step-01-main-cleanup.md) | `Main/` | Clean up Dashboard.tsx | 20 min |
| [10](./main/step-02-canvas-modularization.md) | `Main/` | Split MainCanvas | 25 min |
| [11](./right-sidebar/step-00-reorganization.md) | `RightSidebar/` | Fix folder structure | 15 min |
| [12](./right-sidebar/step-01-split-handlers.md) | `RightSidebar/` | Extract handlers | 30 min |
| [13](./right-sidebar/step-02-top-section.md) | `RightSidebar/` | Config section | 20 min |
| [14](./right-sidebar/step-03-bottom-section.md) | `RightSidebar/` | Tabs section | 20 min |

---

## Current Files

| File | Lines | Issues |
|------|-------|--------|
| `pages/Dashboard.tsx` | 169 | Utility functions mixed in, socket init logic |
| `components/Layout.tsx` | 231 | Theme logic embedded, too many responsibilities |
| `Main/index.tsx` | 278 | Large component (~280 lines), multiple concerns |
| `RightSidebar/index.tsx` | 245 | Mixed mutation logic and UI, nested in Main/components |

---

## Start Here

👉 [Step 1: Layout Cleanup](./layout/step-01-layout-cleanup.md)
