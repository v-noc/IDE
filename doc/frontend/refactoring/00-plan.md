# Frontend Refactoring Plan

## Overview

This is a step-by-step refactoring plan for your v-noc frontend. Each step is a small, focused task that you can complete in one session.

---

## Phase 1: State Management Foundation

| Step | File | Goal | Time |
|------|------|------|------|
| [Step 1](./step-01-query-keys.md) | `src/lib/queryKeys.ts` | Create centralized query keys | 15 min |
| [Step 2](./step-02-code-service.md) | `src/services/code/` | Unify code fetching | 30 min |
| [Step 3](./step-03-logs-service.md) | `src/services/logs/` | Unify logs fetching | 20 min |
| [Step 9](./step-09-react19-patterns.md) | Components | use(), useSuspenseQuery, useOptimistic | 30 min |

## Phase 2: Socket Integration

| Step | File | Goal | Time |
|------|------|------|------|
| [Step 4](./step-04-socket-provider.md) | `src/services/socket/` | Create React context for socket | 25 min |
| [Step 5](./step-05-socket-sync.md) | `src/services/socket/` | Connect socket to React Query | 20 min |

## Phase 3: Canvas Cleanup

| Step | File | Goal | Time |
|------|------|------|------|
| [Step 6](./step-06-split-enhanced-node.md) | `Canvas/components/` | Split EnhancedNode into pieces | 45 min |
| [Step 7](./step-07-canvas-performance.md) | `Canvas/` | Add memoization & lazy loading | 30 min |

## Phase 4: Store Cleanup

| Step | File | Goal | Time |
|------|------|------|------|
| [Step 8](./step-08-project-store-slices.md) | `store/useProjectStore.ts` | Split into slices | 30 min |

---

## How to Use This Plan

1. **Read the step** - Each step explains what, why, and how
2. **Make the changes** - Follow the exact code snippets
3. **Test** - Verify it still works
4. **Commit** - One commit per step for easy rollback
5. **Move to next step**

---

## Start Here

👉 [Step 1: Create Query Keys](./step-01-query-keys.md)
