# Layout Composition

## 🎯 Goal

Create flexible, reusable layout patterns that work like building blocks.

---

## 🏗️ Layout Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Shell                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │                     Navbar                        │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─────────────┬─────────────────────┬───────────────┐  │
│  │             │                     │               │  │
│  │   Sidebar   │       Main          │  RightPanel   │  │
│  │   (Left)    │                     │  (Optional)   │  │
│  │             │                     │               │  │
│  └─────────────┴─────────────────────┴───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Slot-Based Layout Component

### Implementation

```typescript
// components/layouts/DashboardLayout.tsx
import { createContext, useContext, ReactNode } from 'react';

interface LayoutContextValue {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

const LayoutContext = createContext<LayoutContextValue | null>(null);

export const useLayout = () => {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error('Must be used within DashboardLayout');
  return ctx;
};

// Slot components
function Navbar({ children }: { children: ReactNode }) {
  return (
    <header className="layout-navbar">
      {children}
    </header>
  );
}

function Sidebar({ children }: { children: ReactNode }) {
  const { sidebarCollapsed } = useLayout();
  
  return (
    <aside 
      className={`layout-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}
    >
      {children}
    </aside>
  );
}

function Main({ children }: { children: ReactNode }) {
  return (
    <main className="layout-main">
      {children}
    </main>
  );
}

function RightPanel({ children }: { children: ReactNode }) {
  return (
    <aside className="layout-right-panel">
      {children}
    </aside>
  );
}

// Root component
interface DashboardLayoutProps {
  children: ReactNode;
  defaultCollapsed?: boolean;
}

function DashboardLayout({ 
  children, 
  defaultCollapsed = false 
}: DashboardLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(defaultCollapsed);
  
  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev);
  }, []);
  
  return (
    <LayoutContext.Provider value={{ sidebarCollapsed, toggleSidebar }}>
      <div className="dashboard-layout">
        {children}
      </div>
    </LayoutContext.Provider>
  );
}

// Attach slots
DashboardLayout.Navbar = Navbar;
DashboardLayout.Sidebar = Sidebar;
DashboardLayout.Main = Main;
DashboardLayout.RightPanel = RightPanel;

export { DashboardLayout };
```

### Usage

```typescript
// pages/DashboardPage.tsx
import { DashboardLayout } from '@/components/layouts/DashboardLayout';

function DashboardPage() {
  return (
    <DashboardLayout>
      <DashboardLayout.Navbar>
        <Logo />
        <NavigationMenu />
        <UserMenu />
      </DashboardLayout.Navbar>
      
      <DashboardLayout.Sidebar>
        <ProjectTree />
      </DashboardLayout.Sidebar>
      
      <DashboardLayout.Main>
        <Outlet /> {/* React Router nested routes */}
      </DashboardLayout.Main>
      
      <DashboardLayout.RightPanel>
        <NodeDetails />
      </DashboardLayout.RightPanel>
    </DashboardLayout>
  );
}
```

---

## 🎛️ Resizable Panels

Your app uses `react-resizable-panels` - here's how to integrate:

```typescript
// components/layouts/ResizableLayout.tsx
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';

interface ResizableLayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
  rightPanel?: ReactNode;
  defaultSidebarSize?: number;
  defaultRightSize?: number;
}

export function ResizableLayout({
  sidebar,
  main,
  rightPanel,
  defaultSidebarSize = 20,
  defaultRightSize = 25,
}: ResizableLayoutProps) {
  return (
    <PanelGroup direction="horizontal" className="h-full">
      {/* Left Sidebar */}
      <Panel 
        defaultSize={defaultSidebarSize} 
        minSize={15} 
        maxSize={30}
        collapsible
      >
        {sidebar}
      </Panel>
      
      <PanelResizeHandle className="resize-handle" />
      
      {/* Main Content */}
      <Panel defaultSize={rightPanel ? 55 : 80}>
        {main}
      </Panel>
      
      {/* Optional Right Panel */}
      {rightPanel && (
        <>
          <PanelResizeHandle className="resize-handle" />
          <Panel 
            defaultSize={defaultRightSize} 
            minSize={15} 
            maxSize={40}
            collapsible
          >
            {rightPanel}
          </Panel>
        </>
      )}
    </PanelGroup>
  );
}
```

### Usage

```typescript
function DashboardContent() {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  
  return (
    <ResizableLayout
      sidebar={<ProjectTree />}
      main={<CodeEditor />}
      rightPanel={selectedNode ? <NodeDetails node={selectedNode} /> : null}
    />
  );
}
```

---

## 📱 Page Layout Pattern

For pages within the main area:

```typescript
// components/layouts/PageLayout.tsx
interface PageLayoutProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageLayout({
  title,
  description,
  actions,
  children,
}: PageLayoutProps) {
  return (
    <div className="page-layout">
      <header className="page-header">
        <div className="page-header-text">
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
        {actions && (
          <div className="page-header-actions">
            {actions}
          </div>
        )}
      </header>
      
      <div className="page-content">
        {children}
      </div>
    </div>
  );
}

// Usage
function ProjectSettingsPage() {
  return (
    <PageLayout
      title="Project Settings"
      description="Configure your project preferences"
      actions={
        <Button>Save Changes</Button>
      }
    >
      <SettingsForm />
    </PageLayout>
  );
}
```

---

## 🧩 Card Layout

For content sections:

```typescript
// components/layouts/ContentCard.tsx
interface ContentCardProps {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
  padding?: boolean;
}

export function ContentCard({
  title,
  actions,
  children,
  padding = true,
}: ContentCardProps) {
  return (
    <div className="content-card">
      {(title || actions) && (
        <div className="content-card-header">
          {title && <h3>{title}</h3>}
          {actions && <div className="content-card-actions">{actions}</div>}
        </div>
      )}
      <div className={`content-card-body ${padding ? 'with-padding' : ''}`}>
        {children}
      </div>
    </div>
  );
}

// Usage
<ContentCard 
  title="Recent Logs" 
  actions={<Button size="sm">View All</Button>}
>
  <LogsList logs={recentLogs} />
</ContentCard>
```

---

## 📐 CSS for Layouts

```css
/* index.css */

.dashboard-layout {
  display: grid;
  grid-template-rows: auto 1fr;
  grid-template-columns: auto 1fr auto;
  height: 100vh;
}

.layout-navbar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  height: 3.5rem;
  border-bottom: 1px solid var(--border);
}

.layout-sidebar {
  width: 280px;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  transition: width 0.2s ease;
}

.layout-sidebar.collapsed {
  width: 60px;
}

.layout-main {
  overflow-y: auto;
}

.layout-right-panel {
  width: 320px;
  border-left: 1px solid var(--border);
  overflow-y: auto;
}

.resize-handle {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  transition: background 0.2s;
}

.resize-handle:hover {
  background: var(--primary);
}
```

---

## 📖 Next Steps

- **[../dashboard/layout/](../dashboard/layout/)** - Dashboard-specific layout docs
