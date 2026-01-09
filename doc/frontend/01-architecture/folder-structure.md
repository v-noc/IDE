# Folder Structure Guide

## 🎯 Goal

Organize code so you can **find anything in 3 seconds** and **work on one feature without touching others**.

---

## 📁 Recommended Structure

```
src/
├── main.tsx                    # App entry point
├── index.css                   # Global styles
│
├── components/                 # Shared/reusable components
│   ├── ui/                    # Shadcn/primitives (buttons, inputs)
│   └── common/                # App-wide components (ConfirmDialog, etc.)
│
├── features/                   # Feature modules (main code lives here!)
│   ├── Dashboard/             # Dashboard feature
│   │   ├── index.tsx          # Feature entry (exports main component)
│   │   ├── components/        # Dashboard-only components
│   │   ├── hooks/             # Dashboard hooks
│   │   ├── store/             # Zustand stores
│   │   ├── service/           # TanStack Query hooks
│   │   ├── utils/             # Helper functions
│   │   └── features/          # Sub-features
│   │       ├── Main/          # Main content area
│   │       ├── Sidebar/       # Left sidebar
│   │       └── Navbar/        # Top navigation
│   │
│   └── Home/                  # Home page feature
│       └── ...
│
├── hooks/                     # Global/shared hooks
│   └── use-mobile.ts
│
├── lib/                       # Core utilities
│   ├── api.ts                # API client
│   ├── apiRoutes.ts          # API endpoints
│   └── utils.ts              # Generic helpers
│
├── services/                  # Global services
│   ├── socket.ts             # Socket.io singleton
│   └── projectService.ts     # Shared API functions
│
├── store/                     # Global Zustand stores
│   └── appStore.ts           # App-wide state
│
├── types/                     # TypeScript definitions
│   └── project.ts            # Domain types
│
├── routes/                    # Route definitions
│   └── index.tsx
│
└── pages/                     # Page components (route targets)
    └── ...
```

---

## 🧩 The Feature Module Pattern

### What is a Feature?

A **feature** is a self-contained section of your app that:
- Has its own UI components
- Manages its own state
- Fetches its own data
- Can be deleted without breaking other features

### Anatomy of a Feature

```
features/Dashboard/
│
├── index.tsx                  # Public API - what gets exported
│                              # Other features import from here
│
├── components/                # UI Components
│   ├── Layout.tsx            # Main layout wrapper
│   └── CreateGroupsDialog.tsx # Modal component
│
├── hooks/                     # Custom hooks (logic)
│   └── useDashboardLogic.ts  # Feature-specific logic
│
├── store/                     # Zustand stores
│   ├── useProjectStore.ts    # Project selection state
│   └── useThemeStore.ts      # Theme preferences
│
├── service/                   # Data fetching
│   ├── useProject.tsx        # Project queries
│   └── useNode.tsx           # Node queries
│
├── utils/                     # Helper functions
│   └── findNode.ts           # Tree traversal
│
└── features/                  # Nested sub-features
    ├── Main/                  # Main content area
    │   ├── index.tsx         # Sub-feature entry
    │   ├── components/       # Main-specific UI
    │   └── service/          # Main-specific queries
    │
    ├── Sidebar/              # Left sidebar
    │   └── ...
    │
    └── Navbar/               # Top navigation
        └── ...
```

---

## 📐 Naming Conventions

### Files

| Type | Convention | Example |
|------|------------|---------|
| Component | PascalCase | `CreateGroupsDialog.tsx` |
| Hook | camelCase with `use` prefix | `useProjectStore.ts` |
| Utility | camelCase | `findNode.ts` |
| Type | camelCase | `project.ts` |
| Index | `index.tsx` | `index.tsx` |

### Folders

| Type | Convention | Example |
|------|------------|---------|
| Feature | PascalCase | `Dashboard/` |
| Category | lowercase | `components/`, `hooks/` |

---

## 🔄 Import Rules

### ✅ Good Imports

```typescript
// Feature imports from another feature's index
import { Dashboard } from '@/features/Dashboard';

// Importing shared components
import { Button } from '@/components/ui/button';

// Within same feature - use relative paths
import { Layout } from './components/Layout';
import useProjectStore from './store/useProjectStore';
```

### ❌ Bad Imports

```typescript
// Never reach into another feature's internals
import { Layout } from '@/features/Dashboard/components/Layout'; // ❌

// Never import across feature siblings
import { Something } from '../Sidebar/components/Something'; // ❌
```

---

## 📦 When to Create a New Feature vs Sub-Feature

### Create a New Top-Level Feature When:
- It has its own route (e.g., `/dashboard`, `/home`)
- It's a major section of the app
- It has completely different data needs

### Create a Sub-Feature When:
- It's a section within a page (e.g., Sidebar within Dashboard)
- It shares parent's data but has its own components
- It's visually distinct but part of a larger feature

---

## 🎓 Example: Your Current Structure (Refined)

Your `Dashboard` feature currently has this good structure:

```
Dashboard/
├── components/           # Layout, dialogs
├── features/            # Main, Navbar, Sidebar
│   ├── Main/           # Content area
│   │   ├── components/ # Canvas, Code, Docs, etc.
│   │   └── service/    # useCodeElement, useLogs
│   └── Sidebar/        # Tree navigation
├── store/              # useProjectStore, useThemeStore
└── service/            # useProject, useNode, useGroup
```

This mirrors your UI layout - **which is exactly right!**

---

## 📖 Next Steps

Continue to **[02-state-management/overview.md](../02-state-management/overview.md)** to learn how to organize state properly.
