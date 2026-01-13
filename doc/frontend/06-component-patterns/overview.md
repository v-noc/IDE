# Component Patterns Overview

## 🎯 Goal

Design components that are **reusable**, **testable**, and **easy to understand**.

---

## 📚 Patterns Covered

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Container/Presentational** | Separate logic from UI | Data-connected vs pure display |
| **Compound Components** | Complex UI with shared state | Tabs, Accordions, Menus |
| **Composition** | Flexible component assembly | Slot-based layouts |
| **Render Props** | Share behavior, customize UI | Virtualized lists |
| **Custom Hooks** | Share stateful logic | useProjectNavigation |

---

## 1️⃣ Container/Presentational Pattern

### The Idea

Split components into two types:

| Type | Responsibility | Knows About |
|------|----------------|-------------|
| **Container** | Fetches data, manages state | Hooks, stores, APIs |
| **Presentational** | Renders UI | Only props |

### Example

```typescript
// ❌ MIXED: Hard to test, reuse, or understand
function NodeCard() {
  const { data: node, isLoading } = useNode(nodeId);
  const updateNode = useUpdateNode();
  const [isEditing, setIsEditing] = useState(false);
  
  if (isLoading) return <Skeleton />;
  
  return (
    <div className="card">
      <h3>{node.name}</h3>
      {isEditing ? (
        <input value={node.name} onChange={...} />
      ) : (
        <p>{node.description}</p>
      )}
      <button onClick={() => updateNode(node)}>Save</button>
    </div>
  );
}
```

```typescript
// ✅ SPLIT: Clean, testable, reusable

// Presentational - Pure UI, no hooks
interface NodeCardProps {
  node: NodeData;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (node: NodeData) => void;
  onCancel: () => void;
}

function NodeCardUI({
  node,
  isEditing,
  onEdit,
  onSave,
  onCancel,
}: NodeCardProps) {
  return (
    <div className="card">
      <h3>{node.name}</h3>
      {isEditing ? (
        <>
          <input defaultValue={node.name} />
          <button onClick={() => onSave(node)}>Save</button>
          <button onClick={onCancel}>Cancel</button>
        </>
      ) : (
        <>
          <p>{node.description}</p>
          <button onClick={onEdit}>Edit</button>
        </>
      )}
    </div>
  );
}

// Container - All the logic
function NodeCard({ nodeId }: { nodeId: string }) {
  const { data: node, isLoading } = useNode(nodeId);
  const { mutate: updateNode } = useUpdateNode();
  const [isEditing, setIsEditing] = useState(false);
  
  if (isLoading) return <NodeCardSkeleton />;
  if (!node) return null;
  
  return (
    <NodeCardUI
      node={node}
      isEditing={isEditing}
      onEdit={() => setIsEditing(true)}
      onSave={(updated) => {
        updateNode(updated);
        setIsEditing(false);
      }}
      onCancel={() => setIsEditing(false)}
    />
  );
}
```

---

## 2️⃣ Compound Components Pattern

### The Idea

Components that work together and share implicit state.

### Example: Custom Tabs

```typescript
// Usage - clean API
<Tabs defaultValue="code">
  <Tabs.List>
    <Tabs.Trigger value="code">Code</Tabs.Trigger>
    <Tabs.Trigger value="logs">Logs</Tabs.Trigger>
    <Tabs.Trigger value="docs">Docs</Tabs.Trigger>
  </Tabs.List>
  
  <Tabs.Content value="code">
    <CodeEditor />
  </Tabs.Content>
  <Tabs.Content value="logs">
    <LogsViewer />
  </Tabs.Content>
  <Tabs.Content value="docs">
    <DocsEditor />
  </Tabs.Content>
</Tabs>
```

```typescript
// Implementation
import { createContext, useContext, useState } from 'react';

interface TabsContextValue {
  value: string;
  onChange: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabs() {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Must be used within Tabs');
  return context;
}

// Root component
function Tabs({
  defaultValue,
  children,
}: {
  defaultValue: string;
  children: React.ReactNode;
}) {
  const [value, setValue] = useState(defaultValue);
  
  return (
    <TabsContext.Provider value={{ value, onChange: setValue }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

// Sub-components
function TabsList({ children }: { children: React.ReactNode }) {
  return <div className="tabs-list">{children}</div>;
}

function TabsTrigger({
  value,
  children,
}: {
  value: string;
  children: React.ReactNode;
}) {
  const { value: selectedValue, onChange } = useTabs();
  const isActive = value === selectedValue;
  
  return (
    <button
      className={`tab-trigger ${isActive ? 'active' : ''}`}
      onClick={() => onChange(value)}
    >
      {children}
    </button>
  );
}

function TabsContent({
  value,
  children,
}: {
  value: string;
  children: React.ReactNode;
}) {
  const { value: selectedValue } = useTabs();
  
  if (value !== selectedValue) return null;
  return <div className="tab-content">{children}</div>;
}

// Attach sub-components
Tabs.List = TabsList;
Tabs.Trigger = TabsTrigger;
Tabs.Content = TabsContent;

export { Tabs };
```

---

## 3️⃣ Composition with Children & Slots

### The Idea

Instead of passing everything as props, accept `children` or named slots.

```typescript
// ❌ Prop drilling nightmare
<Layout
  navbarContent={<UserMenu />}
  sidebarContent={<ProjectTree />}
  mainContent={<Editor />}
  footerContent={<StatusBar />}
/>

// ✅ Composition with slots
<Layout>
  <Layout.Navbar>
    <UserMenu />
  </Layout.Navbar>
  
  <Layout.Sidebar>
    <ProjectTree />
  </Layout.Sidebar>
  
  <Layout.Main>
    <Editor />
  </Layout.Main>
  
  <Layout.Footer>
    <StatusBar />
  </Layout.Footer>
</Layout>
```

See **[../07-layout-composition/overview.md](../07-layout-composition/overview.md)** for full implementation.

---

## 4️⃣ Custom Hooks Pattern

### The Idea

Extract stateful logic into reusable hooks.

```typescript
// hooks/useNodeSelection.ts
export function useNodeSelection() {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);
  const focusStack = useProjectStore((s) => s.focusStack);
  const pushFocus = useProjectStore((s) => s.pushFocus);
  const popFocus = useProjectStore((s) => s.popFocus);
  
  const canGoBack = focusStack.length > 1;
  
  const selectAndFocus = useCallback((node: AnyNodeTree) => {
    setSelectedNode(node);
    pushFocus(node);
  }, [setSelectedNode, pushFocus]);
  
  const goBack = useCallback(() => {
    if (canGoBack) {
      popFocus();
    }
  }, [canGoBack, popFocus]);
  
  return {
    selectedNode,
    setSelectedNode,
    selectAndFocus,
    goBack,
    canGoBack,
    focusStack,
  };
}

// Usage in any component
function NavigationBreadcrumb() {
  const { focusStack, goBack, canGoBack } = useNodeSelection();
  
  return (
    <div>
      <button disabled={!canGoBack} onClick={goBack}>
        ← Back
      </button>
      {focusStack.map((node) => (
        <span key={node._key}>{node.name} / </span>
      ))}
    </div>
  );
}
```

---

## 📖 Next Steps

- **[container-presentational.md](./container-presentational.md)** - Deep dive
- **[compound-components.md](./compound-components.md)** - Advanced patterns
- **[../07-layout-composition/overview.md](../07-layout-composition/overview.md)** - Layout patterns
