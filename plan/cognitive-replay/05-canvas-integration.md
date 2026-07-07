# Canvas Integration

## Overview

Integrate replay actions with existing ReactFlow canvas in `CanvasView.tsx`.

Actions manipulate the canvas by:
- **Panning** to center on specific nodes
- **Zooming** to focus on details
- **Expanding/collapsing** nodes to show/hide code
- **Highlighting** specific lines of code

---

## Canvas Navigator Hook

Location: `src/frontend/src/features/Dashboard/hooks/useCanvasNavigator.ts`

```typescript
import { useCallback } from 'react';
import type { ReactFlowInstance } from '@xyflow/react';

interface NavigateOptions {
  zoom?: number;
  duration?: number;
}

export function useCanvasNavigator(
  rfInstance: ReactFlowInstance | null
) {
  const panToNode = useCallback((
    nodeKey: string, 
    options: NavigateOptions = {}
  ) => {
    if (!rfInstance) return;
    
    const node = rfInstance.getNode(nodeKey);
    if (!node) return;
    
    const x = node.position.x + (node.measured?.width ?? 0) / 2;
    const y = node.position.y + (node.measured?.height ?? 0) / 2;
    
    rfInstance.setCenter(x, y, {
      zoom: options.zoom ?? 1,
      duration: options.duration ?? 500,
    });
  }, [rfInstance]);

  const fitToNodes = useCallback((
    nodeKeys: string[], 
    options: NavigateOptions = {}
  ) => {
    if (!rfInstance) return;
    rfInstance.fitView({
      nodes: nodeKeys.map(id => ({ id })),
      duration: options.duration ?? 500,
      padding: 0.2,
    });
  }, [rfInstance]);

  return { panToNode, fitToNodes };
}
```

---

## CanvasView Modifications

```diff
// CanvasView.tsx

+ import { useReplayStore } from '@/features/Dashboard/store/slices/replaySlice';
+ import { useCanvasNavigator } from '../hooks/useCanvasNavigator';

const CanvasView = ({ tabId }) => {
+   // Replay state
+   const mode = useReplayStore(s => s.mode);
+   const isPlaying = useReplayStore(s => s.isPlaying);
+   const currentAction = useReplayStore(s => 
+     s.actionQueue[s.currentActionIndex]
+   );
+   const isUserInteracting = useReplayStore(s => s.isUserInteracting);
+   const setUserInteracting = useReplayStore(s => s.setUserInteracting);
+   
+   const { panToNode } = useCanvasNavigator(reactFlowInstanceRef.current);
+   
+   // Pause auto-panning when user manually interacts with canvas
+   const onMoveStart = useCallback(() => {
+     if (isPlaying) setUserInteracting(true);
+   }, [isPlaying, setUserInteracting]);
+   
+   // Execute replay actions
+   useEffect(() => {
+     if (!isPlaying || !currentAction || isUserInteracting) return;
+     
+     switch (currentAction.type) {
+       case 'FOCUS':
+         panToNode(currentAction.nodeKey, { zoom: currentAction.zoom });
+         break;
+       case 'EXPAND':
+         toggleNodeExpansion(tabId, currentAction.nodeKey);
+         break;
+       case 'COLLAPSE':
+         toggleNodeExpansion(tabId, currentAction.nodeKey);
+         break;
+       case 'SELECT':
+         const node = findNodeByKey(projectData, currentAction.nodeKey);
+         if (node) handleNodeSelection(tabId, node, 'primary');
+         break;
+     }
+   }, [currentAction, isPlaying, isUserInteracting]);

    return (
      <ReactFlow
+       onMoveStart={onMoveStart}
        // ... existing props
      >
```

---

## Line Highlighting in EnhancedNode

Location: `EnhancedNode.tsx` or `NodeCodeView.tsx`

```typescript
// Get highlighted lines from replay store
const highlightState = useReplayStore(s => {
  const action = s.actionQueue[s.currentActionIndex];
  if (action?.type === 'HIGHLIGHT' && action.nodeKey === nodeData._key) {
    return { lines: action.lines, color: action.color ?? 'orange' };
  }
  return null;
});

// In render:
{codeLines.map((line, idx) => {
  const lineNum = idx + 1;
  const isHighlighted = highlightState && 
    lineNum >= highlightState.lines[0] && 
    lineNum <= highlightState.lines[1];
  
  return (
    <div
      key={idx}
      className={cn(
        'code-line',
        isHighlighted && 'line-highlighted',
        isHighlighted && `highlight-${highlightState.color}`
      )}
    >
      {line}
    </div>
  );
})}
```

### Highlight Styles

```css
.line-highlighted {
  position: relative;
  transition: background 0.3s ease;
}

.highlight-orange {
  background: linear-gradient(90deg, 
    rgba(251, 146, 60, 0.25) 0%, 
    rgba(251, 146, 60, 0.05) 100%
  );
  border-left: 3px solid #fb923c;
}

.highlight-blue {
  background: rgba(59, 130, 246, 0.15);
  border-left: 3px solid #3b82f6;
}

.highlight-green {
  background: rgba(34, 197, 94, 0.15);
  border-left: 3px solid #22c55e;
}

/* Pulse animation */
@keyframes highlight-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.line-highlighted {
  animation: highlight-pulse 2s ease-in-out infinite;
}
```

---

## Node Focus Animation

Add to `EnhancedNode.tsx`:

```typescript
const isFocused = useReplayStore(s => {
  const action = s.actionQueue[s.currentActionIndex];
  return s.isPlaying && 
    (action?.type === 'FOCUS' || action?.type === 'SELECT') && 
    action.nodeKey === nodeData._key;
});

// In render:
<div className={cn('node-wrapper', isFocused && 'node-focused')}>
```

```css
.node-focused {
  animation: focus-ring 2s ease-in-out infinite;
  border: 2px solid #fbbf24 !important;
}

@keyframes focus-ring {
  0%, 100% { 
    box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.5); 
  }
  50% { 
    box-shadow: 0 0 0 12px rgba(251, 191, 36, 0); 
  }
}
```
