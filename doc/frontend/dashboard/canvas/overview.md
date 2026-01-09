# Canvas Architecture Overview

## 🎯 Goal

Build a **clean**, **performant**, and **scalable** Canvas with code/logs sync across UI.

---

## 📊 Current Architecture

```
                     ┌─────────────────────────┐
                     │       CanvasView        │
                     │  (ReactFlow Provider)   │
                     └───────────┬─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      useNodesState      │
                    │      useEdgesState      │
                    └────────────┬────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │ EnhancedNode │    │ EnhancedNode │    │ EnhancedNode │
    │  (code ⬇️)    │    │  (code ⬇️)    │    │  (code ⬇️)    │
    └──────────────┘    └──────────────┘    └──────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │useEditableCode│   │useEditableCode│   │useEditableCode│
    │  (per node)   │   │  (per node)   │   │  (per node)   │
    └──────────────┘    └──────────────┘    └──────────────┘
```

### Current Issues

| Issue | Impact | Solution |
|-------|--------|----------|
| Each node fetches its own code | N requests for N nodes | Cache with TanStack Query |
| No shared state for code | Save in one place doesn't update canvas | Query invalidation |
| No logs integration | Missing feature | Add `useLogsForNode` hook |
| Complex node component | Hard to maintain | Split into layers |

---

## ✅ Recommended Architecture

### 1. Centralized Query Cache

```
┌─────────────────────────────────────────────────────────┐
│                  TanStack Query Cache                   │
│                                                         │
│  ['code', nodeId1] → { code, file_name, ... }          │
│  ['code', nodeId2] → { code, file_name, ... }          │
│  ['logs', nodeId1] → [{ message, level, ... }, ...]    │
└───────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
      ┌───────────┐   ┌───────────┐   ┌──────────────┐
      │  Canvas   │   │ RightPanel│   │ Code Editor  │
      │  Nodes    │   │   Logs    │   │   (Main)     │
      └───────────┘   └───────────┘   └──────────────┘
```

All consumers use the **same cache** - no duplicate fetching!

### 2. Socket Sync

```
┌─────────────────────────────────────────────────────────┐
│                    Socket Events                        │
│  'code:updated' → queryClient.invalidate(['code',...]) │
│  'logs:new'     → queryClient.invalidate(['logs',...]) │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Recommended Structure

```
features/Dashboard/features/Main/components/Canvas/
├── index.tsx                    # ReactFlowProvider wrapper
├── CanvasView.tsx               # Main canvas container
│
├── components/
│   ├── nodes/                   # Node components (split by type)
│   │   ├── BaseNode.tsx         # Shared node structure
│   │   ├── FunctionNode.tsx     # Function-specific
│   │   ├── CallNode.tsx         # Call-specific  
│   │   ├── ClassNode.tsx        # Class-specific
│   │   └── NodeCode.tsx         # Code display (shared)
│   │
│   ├── edges/
│   │   └── CustomEdge.tsx       # Custom edge styling
│   │
│   └── controls/
│       ├── CanvasToolbar.tsx    # Zoom, fit, etc.
│       └── MiniMap.tsx          # Navigation minimap
│
├── hooks/
│   ├── useCanvasNodes.ts        # Node transformation
│   ├── useCanvasLayout.ts       # Layout algorithm
│   └── useCanvasSync.ts         # Socket event handling
│
└── utils/
    ├── layoutConfig.ts          # Layout constants
    └── nodeColors.ts            # Node styling
```

---

## 🔧 Implementation Guide

See the following docs:
- **[code-logs-sync.md](./code-logs-sync.md)** - How to sync code/logs state
- **[performance.md](./performance.md)** - Memoization, virtualization
- **[node-components.md](./node-components.md)** - Node component patterns
