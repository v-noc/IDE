# Action Schema

> The "language" between AI and UI. Must be simple enough for LLMs to generate reliably.

Location: `src/frontend/src/types/replay.ts`

## Action Types

| Type | Purpose | Visual Effect |
|------|---------|---------------|
| `FOCUS` | Pan camera to node | Smooth camera animation |
| `EXPAND` | Show node's code | Node unfolds with transition |
| `COLLAPSE` | Hide node's code | Node folds back |
| `HIGHLIGHT` | Glow specific lines | Orange line highlighting |
| `SELECT` | Set as selected | Border highlight |
| `NEXT_NODE` | Animated transition | Pulse along edge |
| `WAIT` | Pause point | Timer continues |

## Type Definitions

```typescript
// types/replay.ts

type ActionType = 
  | 'FOCUS' 
  | 'EXPAND' 
  | 'COLLAPSE'
  | 'HIGHLIGHT' 
  | 'SELECT' 
  | 'NEXT_NODE'
  | 'WAIT';

interface BaseAction {
  id: string;
  timestamp: number;    // ms from replay start
  duration: number;     // ms this action takes
  type: ActionType;
  explanation?: string; // Narration for this step
  thought?: string;     // Stream to thinking panel
}

interface FocusAction extends BaseAction {
  type: 'FOCUS';
  nodeKey: string;
  zoom?: number;
}

interface ExpandAction extends BaseAction {
  type: 'EXPAND';
  nodeKey: string;
}

interface CollapseAction extends BaseAction {
  type: 'COLLAPSE';
  nodeKey: string;
}

interface HighlightAction extends BaseAction {
  type: 'HIGHLIGHT';
  nodeKey: string;
  lines: [number, number];  // [start, end] 1-indexed
  color?: 'orange' | 'blue' | 'green';
}

interface SelectAction extends BaseAction {
  type: 'SELECT';
  nodeKey: string;
}

interface NextNodeAction extends BaseAction {
  type: 'NEXT_NODE';
  fromNodeKey: string;
  toNodeKey: string;
}

interface WaitAction extends BaseAction {
  type: 'WAIT';
}

export type ReplayAction = 
  | FocusAction 
  | ExpandAction 
  | CollapseAction
  | HighlightAction 
  | SelectAction
  | NextNodeAction
  | WaitAction;
```

## Example Timeline

```json
[
  {
    "id": "1",
    "timestamp": 0,
    "duration": 3000,
    "type": "FOCUS",
    "nodeKey": "main_function_abc",
    "thought": "Starting at the main entry point...",
    "explanation": "Let's begin where everything starts."
  },
  {
    "id": "2",
    "timestamp": 3000,
    "duration": 2000,
    "type": "EXPAND",
    "nodeKey": "main_function_abc"
  },
  {
    "id": "3",
    "timestamp": 5000,
    "duration": 4000,
    "type": "HIGHLIGHT",
    "nodeKey": "main_function_abc",
    "lines": [5, 7],
    "color": "orange",
    "explanation": "This line calls create_child() to initialize a new instance."
  },
  {
    "id": "4",
    "timestamp": 9000,
    "duration": 3000,
    "type": "NEXT_NODE",
    "fromNodeKey": "main_function_abc",
    "toNodeKey": "create_child_def",
    "thought": "Following the call chain..."
  },
  {
    "id": "5",
    "timestamp": 12000,
    "duration": 2000,
    "type": "SELECT",
    "nodeKey": "create_child_def",
    "explanation": "The create_child function lives here."
  }
]
```

## AI Prompt Template

When requesting actions from AI, use this structure:

```
You are generating a code walkthrough. Output ONLY a JSON array of actions.

Available action types:
- FOCUS: Pan camera to node
- EXPAND: Show node's code  
- HIGHLIGHT: Glow specific lines (provide lines:[start,end])
- SELECT: Set as active node
- NEXT_NODE: Transition between nodes (fromNodeKey, toNodeKey)

Rules:
1. Each action needs: id, timestamp (ms), duration (ms), type
2. Add "thought" for thinking panel, "explanation" for main narration
3. Timestamps must be sequential (timestamp + duration ≤ next.timestamp)
4. Keep durations between 2000-5000ms for readability

User query: "[USER_QUESTION]"
Available nodes: [NODE_LIST]
```
