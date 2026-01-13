# Dashboard Layout

## 🎯 Goal

Understand the Dashboard layout structure and how to compose it cleanly.

---

## 📐 Dashboard Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                          Navbar                                 │
│  [Logo] [Breadcrumb: Project > Folder > File > Fn]   [Actions]  │
├─────────────┬───────────────────────────────┬───────────────────┤
│             │                               │                   │
│   Sidebar   │           Main                │   Right Panel     │
│   (Tree)    │   ┌─────────────────────┐     │   (Details)       │
│             │   │       Tabs          │     │                   │
│   - Files   │   │ [Code][Logs][Docs]  │     │   - Properties    │
│   - Groups  │   ├─────────────────────┤     │   - Actions       │
│   - Calls   │   │                     │     │   - Relations     │
│             │   │   Tab Content       │     │                   │
│             │   │   (Code Editor,     │     │                   │
│             │   │    Logs Viewer,     │     │                   │
│             │   │    Docs Editor)     │     │                   │
│             │   │                     │     │                   │
│             │   └─────────────────────┘     │                   │
│             │                               │                   │
└─────────────┴───────────────────────────────┴───────────────────┘
```

---

## 📁 Recommended File Structure

```
features/Dashboard/
├── index.tsx                    # Public export
├── DashboardPage.tsx            # Route component
│
├── components/
│   ├── DashboardLayout.tsx      # Main layout wrapper
│   └── Breadcrumb.tsx           # Navigation breadcrumb
│
├── features/
│   ├── Navbar/
│   │   ├── index.tsx
│   │   └── components/
│   │       ├── ProjectSelector.tsx
│   │       └── UserMenu.tsx
│   │
│   ├── Sidebar/
│   │   ├── index.tsx
│   │   ├── components/
│   │   │   ├── TreeView.tsx
│   │   │   └── TreeNode.tsx
│   │   └── hooks/
│   │       └── useTreeNavigation.ts
│   │
│   └── Main/
│       ├── index.tsx
│       ├── components/
│       │   ├── ContentTabs.tsx  # Tab container
│       │   ├── Code/
│       │   ├── Logs/
│       │   ├── Docs/
│       │   └── Canvas/
│       └── service/
│           ├── useCode.ts
│           └── useLogs.ts
│
├── store/
│   ├── useProjectStore.ts       # Project navigation state
│   └── useUIStore.ts            # UI preferences
│
└── service/
    └── useProject.tsx           # Project data fetching
```

---

## 🧩 Layout Component

```typescript
// features/Dashboard/components/DashboardLayout.tsx
import { ReactNode } from 'react';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';
import { Navbar } from '../features/Navbar';
import { Sidebar } from '../features/Sidebar';

interface DashboardLayoutProps {
  children: ReactNode;
  rightPanel?: ReactNode;
}

export function DashboardLayout({ 
  children, 
  rightPanel 
}: DashboardLayoutProps) {
  return (
    <div className="dashboard-layout">
      <Navbar />
      
      <div className="dashboard-body">
        <PanelGroup direction="horizontal">
          {/* Sidebar */}
          <Panel defaultSize={20} minSize={15} maxSize={30} collapsible>
            <Sidebar />
          </Panel>
          
          <PanelResizeHandle className="resize-handle" />
          
          {/* Main Content */}
          <Panel defaultSize={rightPanel ? 55 : 80}>
            <main className="dashboard-main">
              {children}
            </main>
          </Panel>
          
          {/* Right Panel (conditional) */}
          {rightPanel && (
            <>
              <PanelResizeHandle className="resize-handle" />
              <Panel defaultSize={25} minSize={15} maxSize={40} collapsible>
                <aside className="dashboard-right-panel">
                  {rightPanel}
                </aside>
              </Panel>
            </>
          )}
        </PanelGroup>
      </div>
    </div>
  );
}
```

---

## 🔗 Dashboard Page (Route Component)

```typescript
// features/Dashboard/DashboardPage.tsx
import { useParams } from 'react-router-dom';
import { DashboardLayout } from './components/DashboardLayout';
import { Main } from './features/Main';
import { RightSidebar } from './features/Main/components/RightSidebar';
import { useProjectTree } from './service/useProject';
import useProjectStore from './store/useProjectStore';
import { useEffect } from 'react';

export function DashboardPage() {
  const { projectKey } = useParams<{ projectKey: string }>();
  const { data: project, isLoading } = useProjectTree(projectKey!);
  const setProjectData = useProjectStore((s) => s.setProjectData);
  const selectedNode = useProjectStore((s) => s.selectedNode);
  
  // Sync project data to store
  useEffect(() => {
    if (project) {
      setProjectData(project);
    }
  }, [project, setProjectData]);
  
  if (isLoading) {
    return <DashboardSkeleton />;
  }
  
  return (
    <DashboardLayout 
      rightPanel={selectedNode ? <RightSidebar node={selectedNode} /> : null}
    >
      <Main />
    </DashboardLayout>
  );
}
```

---

## 📖 Next Page Docs

- **[../code-section/](../code-section/)** - Code editor state & patterns
- **[../sidebar/](../sidebar/)** - Sidebar tree navigation
