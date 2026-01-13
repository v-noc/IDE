# Canvas Node Components

## 🎯 Goal

Split the large `EnhancedNode.tsx` (300+ lines) into **clean**, **testable** components.

---

## 🔧 Current State: One Giant Component

```typescript
// ❌ Current: 300+ lines, mixes all concerns
const EnhancedNode = ({ data }) => {
  // State management
  const [showCode, setShowCode] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  
  // Data fetching
  const { data: codeData } = useEditorCode(...);
  const { editorValue, handleSave, ... } = useEditableCode(...);
  
  // Computed values
  const hasCode = ...;
  const displayCode = ...;
  const statusStyles = useMemo(() => ..., [...]);
  
  // Event handlers
  const handleCopyCode = (e) => { ... };
  const handleSaveClick = (e) => { ... };
  const handleToggleCode = (e) => { ... };
  
  // 200+ lines of JSX...
  return (
    <div className="...">
      {/* Header */}
      {/* Description or Code */}
      {/* Footer */}
      {/* Handles */}
    </div>
  );
};
```

---

## ✅ Recommended: Composable Components

### File Structure

```
components/Canvas/components/nodes/
├── index.ts                    # Export all node types
├── BaseNode.tsx                # Shared wrapper (handles, styling)
├── BaseNode.types.ts           # TypeScript interfaces
│
├── sections/
│   ├── NodeHeader.tsx          # Title, icon, expand button
│   ├── NodeDescription.tsx     # Description text
│   ├── NodeCodeView.tsx        # Code display with editor
│   ├── NodeCodeToolbar.tsx     # Save, copy buttons
│   ├── NodeFooter.tsx          # Timestamps
│   └── NodeLogsIndicator.tsx   # Log count badge
│
├── variants/
│   ├── FunctionNode.tsx        # Function-specific styling
│   ├── CallNode.tsx            # Call-specific styling
│   ├── ClassNode.tsx           # Class-specific styling
│   └── FileNode.tsx            # File-specific styling
│
└── hooks/
    └── useNodeCode.ts          # Code state for nodes
```

---

## 🧩 Component Breakdown

### 1. BaseNode (Wrapper)

```typescript
// components/nodes/BaseNode.tsx
import { memo, ReactNode } from 'react';
import { Handle, Position } from '@xyflow/react';

interface BaseNodeProps {
  children: ReactNode;
  bgColor: string;
  borderColor: string;
  status?: 'error' | 'warning' | 'success' | 'idle';
}

export const BaseNode = memo(function BaseNode({
  children,
  bgColor,
  borderColor,
  status,
}: BaseNodeProps) {
  const statusStyles = getStatusStyles(status);
  
  return (
    <div
      className="min-w-[380px] max-w-[420px] rounded-lg border-2 shadow-lg"
      style={{
        backgroundColor: bgColor,
        borderColor: borderColor,
        ...statusStyles,
      }}
    >
      {children}
      
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
});

function getStatusStyles(status?: string) {
  const colors: Record<string, string> = {
    error: '#ef4444',
    warning: '#f59e0b',
    success: '#10b981',
  };
  
  const color = status ? colors[status] : undefined;
  if (!color) return {};
  
  return {
    borderColor: color,
    boxShadow: `0 0 10px ${color}55`,
  };
}
```

### 2. NodeHeader

```typescript
// components/nodes/sections/NodeHeader.tsx
import { memo, ReactNode } from 'react';
import { ChevronDown, ChevronRight, Code2 } from 'lucide-react';

interface NodeHeaderProps {
  name: string;
  icon: ReactNode;
  iconColor: string;
  borderColor: string;
  bgColor: string;
  
  // Expansion
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  
  // Code toggle
  hasCode?: boolean;
  showCode?: boolean;
  onCodeToggle?: () => void;
  
  // Status
  status?: 'error' | 'warning' | 'success' | 'idle';
}

export const NodeHeader = memo(function NodeHeader({
  name,
  icon,
  iconColor,
  borderColor,
  bgColor,
  expandable,
  expanded,
  onToggle,
  hasCode,
  showCode,
  onCodeToggle,
  status,
}: NodeHeaderProps) {
  return (
    <div 
      className="flex items-center gap-3 border-b px-4 py-3.5 bg-slate-50"
      style={{ borderColor }}
    >
      {expandable && (
        <ExpandButton
          expanded={expanded}
          onClick={onToggle}
          borderColor={borderColor}
          iconColor={iconColor}
          bgColor={bgColor}
        />
      )}
      
      <div className="flex items-center gap-2.5">
        <span className="text-xl" style={{ color: iconColor }}>
          {icon}
        </span>
        <span className="text-base font-bold tracking-wide text-slate-800">
          {name}
        </span>
      </div>
      
      <div className="flex-1" />
      
      {status && status !== 'idle' && (
        <StatusBadge status={status} />
      )}
      
      {hasCode && (
        <CodeToggleButton
          active={showCode}
          onClick={onCodeToggle}
          borderColor={borderColor}
          iconColor={iconColor}
          bgColor={bgColor}
        />
      )}
    </div>
  );
});
```

### 3. NodeCodeView

```typescript
// components/nodes/sections/NodeCodeView.tsx
import { memo, useState, useEffect, lazy, Suspense } from 'react';
import { NodeCodeToolbar } from './NodeCodeToolbar';

const CodeEditor = lazy(() => import('@/components/CodeEditor'));

interface NodeCodeViewProps {
  code: string;
  fileName: string;
  language: string;
  onChange: (code: string) => void;
  onSave: () => void;
  hasChanges: boolean;
  isSaving: boolean;
  isLoading: boolean;
  borderColor: string;
  iconColor: string;
}

export const NodeCodeView = memo(function NodeCodeView({
  code,
  fileName,
  language,
  onChange,
  onSave,
  hasChanges,
  isSaving,
  isLoading,
  borderColor,
  iconColor,
}: NodeCodeViewProps) {
  return (
    <div className="border-t bg-slate-50" style={{ borderColor }}>
      <NodeCodeToolbar
        fileName={fileName}
        hasChanges={hasChanges}
        isSaving={isSaving}
        onSave={onSave}
        onCopy={() => navigator.clipboard.writeText(code)}
        iconColor={iconColor}
        borderColor={borderColor}
      />
      
      <div className="h-[300px] overflow-hidden nodrag">
        <Suspense fallback={<CodeSkeleton />}>
          <CodeEditor
            language={language}
            value={code}
            onChange={onChange}
            isLoading={isLoading}
            options={{
              minimap: { enabled: false },
              fontSize: 12,
              scrollBeyondLastLine: false,
            }}
          />
        </Suspense>
      </div>
    </div>
  );
});
```

### 4. Complete Node Assembly

```typescript
// components/nodes/variants/FunctionNode.tsx
import { memo } from 'react';
import { BaseNode } from '../BaseNode';
import { NodeHeader } from '../sections/NodeHeader';
import { NodeDescription } from '../sections/NodeDescription';
import { NodeCodeView } from '../sections/NodeCodeView';
import { NodeFooter } from '../sections/NodeFooter';
import { useNodeCode } from '../hooks/useNodeCode';
import { FunctionIcon } from 'lucide-react';

interface FunctionNodeData {
  nodeId: string;
  name: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
}

export const FunctionNode = memo(function FunctionNode({
  data,
}: {
  data: FunctionNodeData;
}) {
  const {
    showCode,
    setShowCode,
    code,
    localCode,
    setLocalCode,
    hasChanges,
    isSaving,
    isLoading,
    handleSave,
    fileName,
    language,
  } = useNodeCode(data.nodeId);
  
  const hasCode = !!code;
  
  // Function-specific colors
  const colors = {
    bg: '#fef3c7',
    border: '#fbbf24',
    icon: '#d97706',
    text: '#78350f',
  };
  
  return (
    <BaseNode bgColor={colors.bg} borderColor={colors.border}>
      <NodeHeader
        name={data.name}
        icon={<FunctionIcon size={18} />}
        iconColor={colors.icon}
        borderColor={colors.border}
        bgColor={colors.bg}
        expandable={data.expandable}
        expanded={data.expanded}
        onToggle={data.onToggle}
        hasCode={hasCode}
        showCode={showCode}
        onCodeToggle={() => setShowCode(!showCode)}
      />
      
      {showCode && hasCode ? (
        <NodeCodeView
          code={localCode}
          fileName={fileName}
          language={language}
          onChange={setLocalCode}
          onSave={handleSave}
          hasChanges={hasChanges}
          isSaving={isSaving}
          isLoading={isLoading}
          borderColor={colors.border}
          iconColor={colors.icon}
        />
      ) : (
        <NodeDescription description={data.description} />
      )}
      
      <NodeFooter
        createdAt={data.createdAt}
        updatedAt={data.updatedAt}
        borderColor={colors.border}
        iconColor={colors.icon}
      />
    </BaseNode>
  );
});
```

---

## 🎣 useNodeCode Hook

```typescript
// components/nodes/hooks/useNodeCode.ts
import { useState, useEffect, useMemo } from 'react';
import { useCode, useWriteCode } from '@/services/code/useCode';
import { detectLanguage } from '@/components/CodeEditor/detectLanguage';

export function useNodeCode(nodeId: string) {
  const [showCode, setShowCode] = useState(false);
  
  // Only fetch when code is visible
  const { data: codeData, isLoading } = useCode(
    showCode ? nodeId : undefined
  );
  
  const { mutate: writeCode, isPending: isSaving } = useWriteCode();
  
  // Local editing state
  const [localCode, setLocalCode] = useState(codeData?.code ?? '');
  
  // Sync with server code
  useEffect(() => {
    if (codeData?.code) {
      setLocalCode(codeData.code);
    }
  }, [codeData?.code]);
  
  const code = codeData?.code;
  const hasChanges = localCode !== code;
  const fileName = codeData?.file_name ?? '';
  const language = detectLanguage(fileName);
  
  const handleSave = () => {
    if (nodeId && localCode) {
      writeCode({ nodeId, code: localCode });
    }
  };
  
  return {
    showCode,
    setShowCode,
    code,
    localCode,
    setLocalCode,
    hasChanges,
    isSaving,
    isLoading,
    handleSave,
    fileName,
    language,
  };
}
```

---

## 📝 Node Type Registration

```typescript
// components/nodes/index.ts
import { FunctionNode } from './variants/FunctionNode';
import { CallNode } from './variants/CallNode';
import { ClassNode } from './variants/ClassNode';
import { FileNode } from './variants/FileNode';

// Single export for React Flow
export const nodeTypes = {
  function: FunctionNode,
  call: CallNode,
  class: ClassNode,
  file: FileNode,
} as const;

export type NodeType = keyof typeof nodeTypes;
```

```typescript
// CanvasView.tsx
import { nodeTypes } from './components/nodes';

function CanvasView() {
  return (
    <ReactFlow
      nodeTypes={nodeTypes}
      // ...
    />
  );
}
```

---

## ✅ Benefits of This Structure

| Before | After |
|--------|-------|
| 318 lines in one file | ~50 lines per component |
| Hard to test | Easy to unit test each piece |
| One change = risk everywhere | Isolated changes |
| Difficult to add node types | Add new variant easily |
| Code fetching mixed in | Clean hook abstraction |
