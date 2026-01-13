# Step 6: Split EnhancedNode

## Goal
Break the 318-line `EnhancedNode.tsx` into smaller, focused components.

## Why
The current file mixes:
- Data fetching (useEditorCode, useEditableCode)
- State management (showCode, copiedCode)
- Event handlers (handleCopyCode, handleSave)
- 200+ lines of JSX

This makes it hard to maintain, test, and optimize.

---

## Strategy

Split into this structure:
```
Canvas/components/nodes/
├── EnhancedNode.tsx          # Keep as main entry (simplified)
├── NodeHeader.tsx            # Header with name, icon, buttons
├── NodeDescription.tsx       # Description section
├── NodeCodeView.tsx          # Code editor section
├── NodeCodeToolbar.tsx       # Save/Copy buttons
├── NodeFooter.tsx            # Timestamps
└── useNodeCode.ts            # Hook for code state
```

---

## Step 6a: Extract `useNodeCode.ts`

Create a hook that handles all code-related logic:

### NEW: `Canvas/components/nodes/useNodeCode.ts`

```typescript
import { useState, useEffect } from 'react';
import { useCode, useWriteCode } from '@/services/code';
import { detectLanguage } from '@/components/CodeEditor/detectLanguage';

export interface UseNodeCodeOptions {
  nodeId: string;
  targetKey?: string; // For call nodes
  nodeType?: string;
}

export function useNodeCode({ nodeId, targetKey, nodeType }: UseNodeCodeOptions) {
  const [showCode, setShowCode] = useState(false);

  // Use target key for call nodes
  const effectiveId = nodeType === 'call' && targetKey ? targetKey : nodeId;

  // Only fetch when code is visible
  const { data: codeData, isLoading, isError } = useCode(
    showCode ? effectiveId : undefined
  );

  const { mutate: writeCode, isPending: isSaving } = useWriteCode();

  // Local editing state
  const [localCode, setLocalCode] = useState('');

  // Sync with server code
  useEffect(() => {
    if (codeData?.code) {
      setLocalCode(codeData.code);
    }
  }, [codeData?.code]);

  const hasChanges = codeData?.code !== localCode;
  const hasCode = !!codeData?.code || localCode.length > 0;
  const fileName = codeData?.file_name ?? '';
  const language = detectLanguage(fileName);

  const handleSave = () => {
    if (effectiveId && localCode) {
      writeCode({ elementId: effectiveId, code: localCode });
    }
  };

  const toggleCode = () => setShowCode(prev => !prev);

  return {
    showCode,
    toggleCode,
    hasCode,
    code: localCode,
    setCode: setLocalCode,
    hasChanges,
    isSaving,
    isLoading,
    isError,
    fileName,
    language,
    handleSave,
  };
}
```

---

## Step 6b: Extract `NodeHeader.tsx`

### NEW: `Canvas/components/nodes/NodeHeader.tsx`

```typescript
import { memo, ReactNode } from 'react';
import { ChevronDown, ChevronRight, Code2 } from 'lucide-react';

interface NodeHeaderProps {
  name: string;
  icon: ReactNode;
  iconColor: string;
  borderColor: string;
  bgColor: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  hasCode?: boolean;
  showCode?: boolean;
  onCodeToggle?: () => void;
  status?: 'error' | 'warning' | 'success' | 'idle';
}

const statusColors: Record<string, string> = {
  error: '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
};

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
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle?.();
          }}
          className="flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all hover:scale-110"
          style={{
            borderColor,
            color: iconColor,
            backgroundColor: expanded ? iconColor : bgColor,
          }}
        >
          {expanded 
            ? <ChevronDown size={18} style={{ color: bgColor }} />
            : <ChevronRight size={18} />
          }
        </button>
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
        <span
          className="h-3 w-3 rounded-full ring-2 ring-white"
          style={{ backgroundColor: statusColors[status] }}
        />
      )}

      {hasCode && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onCodeToggle?.();
          }}
          className="flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all hover:scale-110"
          style={{
            borderColor,
            backgroundColor: showCode ? iconColor : bgColor,
            color: showCode ? bgColor : iconColor,
          }}
        >
          <Code2 size={16} />
        </button>
      )}
    </div>
  );
});
```

---

## Step 6c: Simplified `EnhancedNode.tsx`

Now the main component is much cleaner:

```typescript
// Canvas/components/nodes/EnhancedNode.tsx
import React, { memo, useMemo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { NodeHeader } from './NodeHeader';
import { NodeDescription } from './NodeDescription';
import { NodeCodeView } from './NodeCodeView';
import { NodeFooter } from './NodeFooter';
import { useNodeCode } from './useNodeCode';

export interface EnhancedNodeData {
  name: string;
  mainIcon: React.ReactNode;
  bgColor: string;
  textColor: string;
  iconColor: string;
  borderColor: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  metadata?: {
    createdAt?: string;
    updatedAt?: string;
    status?: 'error' | 'warning' | 'success' | 'idle';
    description?: string;
  };
  nodeId?: string;
  nodeType?: string;
  target?: { _key: string };
}

const EnhancedNode = memo(function EnhancedNode({
  data,
}: {
  data: EnhancedNodeData;
}) {
  const nodeCode = useNodeCode({
    nodeId: data.nodeId ?? '',
    targetKey: data.target?._key,
    nodeType: data.nodeType,
  });

  const statusStyles = useMemo(() => {
    const status = data.metadata?.status;
    if (!status || status === 'idle') return {};
    const colors: Record<string, string> = {
      error: '#ef4444',
      warning: '#f59e0b',
      success: '#10b981',
    };
    return {
      borderColor: colors[status],
      boxShadow: `0 0 10px ${colors[status]}55`,
    };
  }, [data.metadata?.status]);

  return (
    <div
      className="relative min-w-[380px] max-w-[420px] overflow-hidden rounded-lg border-2 shadow-lg bg-white"
      style={{
        backgroundColor: data.bgColor,
        borderColor: data.borderColor,
        ...statusStyles,
      }}
    >
      <NodeHeader
        name={data.name}
        icon={data.mainIcon}
        iconColor={data.iconColor}
        borderColor={data.borderColor}
        bgColor={data.bgColor}
        expandable={data.expandable}
        expanded={data.expanded}
        onToggle={data.onToggle}
        hasCode={nodeCode.hasCode}
        showCode={nodeCode.showCode}
        onCodeToggle={nodeCode.toggleCode}
        status={data.metadata?.status}
      />

      {nodeCode.showCode ? (
        <NodeCodeView
          code={nodeCode.code}
          fileName={nodeCode.fileName}
          language={nodeCode.language}
          onChange={nodeCode.setCode}
          onSave={nodeCode.handleSave}
          hasChanges={nodeCode.hasChanges}
          isSaving={nodeCode.isSaving}
          isLoading={nodeCode.isLoading}
          borderColor={data.borderColor}
          iconColor={data.iconColor}
        />
      ) : (
        <NodeDescription description={data.metadata?.description} />
      )}

      <NodeFooter
        createdAt={data.metadata?.createdAt}
        updatedAt={data.metadata?.updatedAt}
        borderColor={data.borderColor}
        iconColor={data.iconColor}
      />

      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
});

export default EnhancedNode;
```

---

## Missing Components

Create these small components (simple extraction from original):

- `NodeDescription.tsx` - Just the description paragraph
- `NodeCodeView.tsx` - Code editor + toolbar
- `NodeFooter.tsx` - Timestamps

See `doc/frontend/dashboard/canvas/node-components.md` for full code.

---

## Verification

- [ ] Canvas nodes still render
- [ ] Code toggle still works
- [ ] Save still works
- [ ] No TypeScript errors

---

## Next Step

👉 [Step 7: Add Canvas Performance](./step-07-canvas-performance.md)
