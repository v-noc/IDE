# Code Section

## 🎯 Goal

Handle code display, editing, and state management for the code editor.

---

## 📊 Code State Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    User Selects Node                         │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              useProjectStore.setSelectedNode                │
│              (Updates selectedNode in Zustand)               │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              useCode(selectedNode._key)                      │
│              (Fetches code from API via TanStack Query)      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              <CodeEditor code={data.code} />                 │
│              (Monaco renders the code)                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
features/Dashboard/features/Main/components/Code/
├── index.tsx              # Container component
├── CodeEditor.tsx         # Presentational (Monaco wrapper)
├── CodeToolbar.tsx        # Save, format, run buttons
├── hooks/
│   ├── useEditableCode.ts # Local editing state
│   └── useEditorConfig.ts # Monaco configuration
└── utils/
    └── codeHighlight.ts   # Syntax highlighting helpers
```

---

## 🔧 Code Service (TanStack Query)

```typescript
// services/code/useCode.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';
import { api } from '@/lib/api';

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  code: string;
}

// Fetch code for any element
export const useCode = (elementId: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.code.detail(elementId ?? ''),
    queryFn: () => api<CodeData>(`/code-elements/${elementId}/code`),
    enabled: !!elementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Write/save code
export const useWriteCode = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ elementId, code }: { elementId: string; code: string }) =>
      api(`/code-elements/${elementId}/write-code`, {
        method: 'POST',
        body: { code },
      }),
    onSuccess: (_, { elementId }) => {
      // Invalidate code cache
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(elementId),
      });
      
      // Also invalidate project tree (code changes might affect structure)
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.all,
      });
    },
  });
};
```

---

## 🎨 Code Editor Components

### Container Component

```typescript
// components/Code/index.tsx
import { useCode, useWriteCode } from '@/services/code/useCode';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { CodeEditor } from './CodeEditor';
import { CodeToolbar } from './CodeToolbar';
import { useEditableCode } from './hooks/useEditableCode';

export function Code() {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const { data: codeData, isLoading, error } = useCode(selectedNode?._key);
  const { mutate: writeCode, isPending: isSaving } = useWriteCode();
  
  const {
    localCode,
    setLocalCode,
    isDirty,
    resetCode,
  } = useEditableCode(codeData?.code);
  
  if (isLoading) return <CodeSkeleton />;
  if (error) return <CodeError error={error} />;
  if (!codeData) return <EmptyState message="Select a code element" />;
  
  const handleSave = () => {
    if (selectedNode && localCode) {
      writeCode(
        { elementId: selectedNode._key, code: localCode },
        { onSuccess: () => resetCode(localCode) }
      );
    }
  };
  
  return (
    <div className="code-section">
      <CodeToolbar
        fileName={codeData.file_name}
        isDirty={isDirty}
        isSaving={isSaving}
        onSave={handleSave}
        onReset={() => resetCode(codeData.code)}
      />
      <CodeEditor
        code={localCode}
        language={detectLanguage(codeData.file_name)}
        onChange={setLocalCode}
        readOnly={isSaving}
      />
    </div>
  );
}
```

### Presentational Editor

```typescript
// components/Code/CodeEditor.tsx
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  code: string;
  language: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
}

export function CodeEditor({
  code,
  language,
  onChange,
  readOnly = false,
}: CodeEditorProps) {
  return (
    <Editor
      height="100%"
      language={language}
      value={code}
      onChange={(value) => onChange(value ?? '')}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 2,
      }}
      theme="vs-dark"
    />
  );
}
```

---

## 🎣 useEditableCode Hook

```typescript
// components/Code/hooks/useEditableCode.ts
import { useState, useEffect, useMemo } from 'react';

export function useEditableCode(serverCode: string | undefined) {
  const [localCode, setLocalCode] = useState(serverCode ?? '');
  
  // Sync when server code changes (initial load or external update)
  useEffect(() => {
    if (serverCode !== undefined) {
      setLocalCode(serverCode);
    }
  }, [serverCode]);
  
  // Track if local differs from server
  const isDirty = useMemo(() => {
    return localCode !== (serverCode ?? '');
  }, [localCode, serverCode]);
  
  // Reset to specific value
  const resetCode = (newCode: string) => {
    setLocalCode(newCode);
  };
  
  return {
    localCode,
    setLocalCode,
    isDirty,
    resetCode,
  };
}
```

---

## ⌨️ Keyboard Shortcuts

```typescript
// Integrate with Monaco's key bindings
function CodeEditor({ onSave, ... }) {
  const handleEditorMount = (editor: Monaco.editor.IStandaloneCodeEditor) => {
    // Ctrl/Cmd + S to save
    editor.addAction({
      id: 'save-code',
      label: 'Save Code',
      keybindings: [
        monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
      ],
      run: () => {
        onSave();
      },
    });
  };
  
  return (
    <Editor
      onMount={handleEditorMount}
      // ...
    />
  );
}
```

---

## 📖 Next Steps

- **[../sidebar/](../sidebar/)** - Sidebar tree navigation
