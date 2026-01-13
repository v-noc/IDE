# Frontend Architecture Overview

## 🎯 Goals

This documentation guides you through refactoring the v-noc frontend to be:

1. **Clean & Maintainable** - Easy to understand and modify
2. **Modular** - Each feature is self-contained
3. **Scalable** - Can grow without becoming messy
4. **Professional** - Follows React 19 best practices

---

## 📚 How to Use This Documentation

### Reading Order (Recommended)

```
1. This Introduction (you're here!)
2. 01-architecture/folder-structure.md    → Understand project layout
3. 02-state-management/overview.md        → Master state patterns
4. 03-data-fetching/tanstack-query.md     → Learn data fetching
5. 04-socket-realtime/socket-integration.md → Understand real-time
6. 06-component-patterns/overview.md      → Component design
7. 07-layout-composition/overview.md      → Layout patterns
8. Feature-specific guides (dashboard/, home/)
```

### Each Guide Answers

- **What?** - What is this pattern/concept?
- **Why?** - Why use it? What problem does it solve?
- **How?** - Step-by-step with code examples
- **When?** - When to use vs. alternatives

---

## 🏗️ Current Architecture Summary

### Tech Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| UI | React 19 | Component library |
| Build | Vite | Fast dev server & bundling |
| Routing | React Router 7 | Page navigation |
| UI Components | Radix UI + Shadcn | Accessible primitives |
| State (UI) | Zustand + Immer | Client-side state |
| State (Server) | TanStack Query | Data fetching & caching |
| Real-time | Socket.io Client | WebSocket communication |
| Flow Diagrams | XYFlow | Graph visualization |

### Current Folder Pattern

Your codebase uses a **Feature-First** pattern where each UI section has its own:
- `components/` - UI pieces
- `hooks/` - Custom React hooks
- `service/` - Data fetching (TanStack Query)
- `store/` - Local state (Zustand)
- `utils/` - Helper functions

This is a **good foundation** - we'll refine it, not replace it.

---

## 🔑 Key Principles

### 1. Separate Concerns

```
┌─────────────────────────────────────────────────┐
│                   Component                     │
│  (Renders UI, handles user events)              │
├─────────────────────────────────────────────────┤
│                     Hooks                       │
│  (Encapsulates logic, connects to stores/APIs)  │
├──────────────────────┬──────────────────────────┤
│    Zustand Store     │    TanStack Query        │
│    (UI State)        │    (Server State)        │
├──────────────────────┴──────────────────────────┤
│              Socket.io Service                  │
│              (Real-time Updates)                │
└─────────────────────────────────────────────────┘
```

### 2. Single Responsibility

Each file/module does ONE thing well:
- **Component** → Renders UI
- **Hook** → Manages logic
- **Store** → Holds state
- **Service** → Fetches data

### 3. Colocation

Keep related code together:
```
features/Dashboard/
├── components/       # Dashboard-specific UI
├── hooks/           # Dashboard-specific hooks
├── store/           # Dashboard state (Zustand)
├── service/         # Dashboard API calls
└── features/        # Sub-features (Main, Sidebar, etc.)
```

---

## 📋 Refactoring Roadmap

### Phase 1: Foundation ✅
- [x] Analyze current codebase
- [x] Create documentation structure

### Phase 2: State Management
- [ ] Clean up Zustand stores (slice pattern)
- [ ] Standardize TanStack Query usage
- [ ] Implement shared state patterns

### Phase 3: Component Patterns
- [ ] Apply Container/Presentational pattern
- [ ] Create reusable compound components
- [ ] Standardize layout composition

### Phase 4: Feature Cleanup
- [ ] Refactor Dashboard feature
- [ ] Refactor Home feature
- [ ] Clean up shared components

---

## 📖 Next Steps

Start with **[01-architecture/folder-structure.md](../01-architecture/folder-structure.md)** to understand the recommended project layout.
