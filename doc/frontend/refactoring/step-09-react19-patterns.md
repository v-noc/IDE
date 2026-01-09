# React 19 Modern Patterns

## Goal
Use React 19's new APIs to eliminate boilerplate.

---

## 1. The `use()` Hook

React 19 introduces `use()` - a hook that can read promises and context directly.

### Before: useEffect + useState for Data

```typescript
// ❌ OLD: Lots of boilerplate
function CodeViewer({ nodeId }: { nodeId: string }) {
  const [code, setCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchCode(nodeId)
      .then(setCode)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [nodeId]);

  if (loading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  return <CodeEditor value={code ?? ''} />;
}
```

### After: use() with Suspense

```typescript
// ✅ NEW: Clean with use()
import { use, Suspense } from 'react';

function CodeViewer({ nodeId }: { nodeId: string }) {
  const codePromise = fetchCode(nodeId);
  const code = use(codePromise); // Suspends until resolved
  
  return <CodeEditor value={code} />;
}

// Wrap with Suspense + ErrorBoundary
function CodeSection({ nodeId }: { nodeId: string }) {
  return (
    <ErrorBoundary fallback={<ErrorMessage />}>
      <Suspense fallback={<Skeleton />}>
        <CodeViewer nodeId={nodeId} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

---

## 2. use() with Context

### Before: useContext

```typescript
// ❌ OLD
import { useContext } from 'react';

function Component() {
  const socket = useContext(SocketContext);
  if (!socket) throw new Error('No socket context');
  // ...
}
```

### After: use()

```typescript
// ✅ NEW: Can use conditionally!
import { use } from 'react';

function Component({ needsSocket }: { needsSocket: boolean }) {
  // use() can be called conditionally - useContext cannot!
  const socket = needsSocket ? use(SocketContext) : null;
  // ...
}
```

---

## 3. useSuspenseQuery (TanStack Query)

TanStack Query v5+ supports Suspense mode natively:

### Before: Manual Loading States

```typescript
// ❌ OLD: Check loading/error every time
function ProjectTree({ projectId }: { projectId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  });

  if (isLoading) return <TreeSkeleton />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return null;

  return <Tree nodes={data.children} />;
}
```

### After: useSuspenseQuery

```typescript
// ✅ NEW: No loading checks!
import { useSuspenseQuery } from '@tanstack/react-query';

function ProjectTree({ projectId }: { projectId: string }) {
  const { data } = useSuspenseQuery({
    queryKey: queryKeys.projects.tree(projectId),
    queryFn: () => fetchProject(projectId),
  });

  // data is guaranteed to exist!
  return <Tree nodes={data.children} />;
}

// Parent handles loading/error
function DashboardPage() {
  return (
    <ErrorBoundary fallback={<TreeError />}>
      <Suspense fallback={<TreeSkeleton />}>
        <ProjectTree projectId={projectId} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

---

## 4. useOptimistic for Instant UI

### Before: Manual Optimistic Updates

```typescript
// ❌ OLD
function SaveButton({ code, nodeId }) {
  const [isSaving, setIsSaving] = useState(false);
  const [displayedCode, setDisplayedCode] = useState(code);

  const handleSave = async () => {
    setIsSaving(true);
    setDisplayedCode(code); // Optimistic
    try {
      await saveCode(nodeId, code);
    } catch {
      setDisplayedCode(previousCode); // Rollback
    }
    setIsSaving(false);
  };
}
```

### After: useOptimistic

```typescript
// ✅ NEW: Built-in optimistic state
import { useOptimistic, useTransition } from 'react';

function CodeSection({ nodeId, serverCode }) {
  const [isPending, startTransition] = useTransition();
  const [optimisticCode, setOptimisticCode] = useOptimistic(serverCode);

  const handleSave = (newCode: string) => {
    startTransition(async () => {
      setOptimisticCode(newCode); // Instant update
      await saveCode(nodeId, newCode); // Actual API call
      // Auto-reverts if throws
    });
  };

  return (
    <CodeEditor
      value={optimisticCode}
      onSave={handleSave}
      disabled={isPending}
    />
  );
}
```

---

## 5. useFormStatus for Forms

### Before: Manual Form State

```typescript
// ❌ OLD
function BasicInfoForm({ onSubmit }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    await onSubmit(formData);
    setIsSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input disabled={isSubmitting} />
      <button disabled={isSubmitting}>
        {isSubmitting ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
}
```

### After: useFormStatus

```typescript
// ✅ NEW: Form status from context
import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button disabled={pending}>
      {pending ? 'Saving...' : 'Save'}
    </button>
  );
}

function BasicInfoForm({ action }) {
  return (
    <form action={action}>
      <input name="name" />
      <SubmitButton /> {/* Auto-knows form state! */}
    </form>
  );
}
```

---

## 6. useActionState for Form Actions

### Before: useState + Handler

```typescript
// ❌ OLD
function NodeEditor() {
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  const handleSubmit = async (formData: FormData) => {
    setIsPending(true);
    setError(null);
    try {
      await updateNode(formData);
    } catch (e) {
      setError(e.message);
    }
    setIsPending(false);
  };
}
```

### After: useActionState

```typescript
// ✅ NEW: Action state management
import { useActionState } from 'react';

async function updateNodeAction(
  prevState: { error: string | null },
  formData: FormData
) {
  try {
    await updateNode(formData);
    return { error: null };
  } catch (e) {
    return { error: e.message };
  }
}

function NodeEditor() {
  const [state, formAction, isPending] = useActionState(
    updateNodeAction,
    { error: null }
  );

  return (
    <form action={formAction}>
      {state.error && <ErrorMessage>{state.error}</ErrorMessage>}
      <input name="name" disabled={isPending} />
      <button disabled={isPending}>Save</button>
    </form>
  );
}
```

---

## 7. Ref Cleanup Functions

### Before: useEffect for Cleanup

```typescript
// ❌ OLD
function ResizablePanel({ onResize }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new ResizeObserver(onResize);
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [onResize]);

  return <div ref={ref} />;
}
```

### After: Ref Callbacks with Cleanup

```typescript
// ✅ NEW: Return cleanup from ref callback
function ResizablePanel({ onResize }) {
  return (
    <div
      ref={(node) => {
        if (!node) return;
        const observer = new ResizeObserver(onResize);
        observer.observe(node);
        return () => observer.disconnect(); // Cleanup!
      }}
    />
  );
}
```

---

## Summary: Boilerplate Reduction

| Pattern | Before | After |
|---------|--------|-------|
| Data fetching | useState + useEffect + loading/error | use() + Suspense |
| Query loading | if (loading) return... | useSuspenseQuery |
| Optimistic UI | Manual state + rollback | useOptimistic |
| Form submission | useState(isPending) | useFormStatus |
| Form actions | useState + handler | useActionState |
| Ref cleanup | useEffect | Ref callback return |

---

## Apply to Your Codebase

### 1. Canvas Nodes - useSuspenseQuery

```typescript
// Canvas/components/nodes/CanvasNode.tsx
const CanvasNode = memo(function CanvasNode({ data }) {
  // Use suspense query - parent handles loading
  const { data: codeData } = useSuspenseQuery({
    queryKey: queryKeys.code.detail(data.nodeId),
    queryFn: () => codeApi.getCode(data.nodeId),
  });

  return <NodeUI code={codeData.code} />;
});

// Wrap nodes with Suspense
<Suspense fallback={<NodeSkeleton />}>
  <CanvasNode data={nodeData} />
</Suspense>
```

### 2. Right Sidebar Forms - useActionState

```typescript
// RightSidebar/components/BasicInfoForm.tsx
async function updateInfoAction(prev, formData: FormData) {
  await api.updateNode(formData.get('nodeId'), {
    name: formData.get('name'),
    description: formData.get('description'),
  });
  return { success: true };
}

function BasicInfoForm({ nodeId }) {
  const [state, action, isPending] = useActionState(updateInfoAction, {});
  
  return (
    <form action={action}>
      <input type="hidden" name="nodeId" value={nodeId} />
      <Input name="name" disabled={isPending} />
      <Textarea name="description" disabled={isPending} />
      <Button disabled={isPending}>Save</Button>
    </form>
  );
}
```
