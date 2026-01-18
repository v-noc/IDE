# Step 2: Frontend Flame Chart Component (Simple & Lightweight)

## Goal
Implement a lightweight Flame Chart inspired by `react-flame-graph`.
Reference: https://github.com/bvaughn/react-flame-graph

## Design Philosophy
- **Simple**: No heavy charting libraries (D3, etc.).
- **Efficient**: Use absolute positioning and simple math for layout.
- **Interactive**: Scroll to zoom (optional), Click to focus.

## Implementation Details

### 1. Data Structure transforms
Transform `LogTreeNode` to a `FlameGraphNode` format compatible with the rendering logic:
```typescript
interface FlameGraphNode {
  name: string;
  value: number; // duration
  children?: FlameGraphNode[];
  tooltip?: string;
  backgroundColor?: string;
  color?: string;
  id: string; // for click handling
  depth: number;
  start: number; // relative start time
}
```

### 2. Component: `FlameGraph.tsx`
**File:** `src/frontend/src/features/Dashboard/features/Main/components/Sandbox/features/Logs/components/FlameChart.tsx`

**Props:**
- `data`: Root LogNode (or wrapper)
- `width`: number (container width)
- `height`: number (row height * max depth)
- `onChange`: (node: FlameGraphNode) => void

**Rendering Logic:**
 Instead of recursion (which can get deep), use a **flat list of renderable items** calculated once:
1.  **Flatten Tree**: Traverse the tree to generate a list of `{ node, x, y, width }`.
    -   `x` = `(node.startTime - root.startTime) / root.duration * totalWidth`
    -   `y` = `node.depth * rowHeight`
    -   `width` = `node.duration / root.duration * totalWidth`
2.  **Render**: simple `div`s with `absolute` positioning.
    -   Use `Code` font for labels.
    -   Text overflow ellipsis.
    -   Background color: Deterministic hash of `node.name` (function name) to keep it consistent.

### 3. Utils
**File:** `src/frontend/src/features/Dashboard/features/Main/components/Sandbox/features/Logs/utils/flameGraphUtils.ts`
- `getItemData(node, depth, start, scale)`: Recursive helper to build render list.
- `stringToColor(str)`: Helper to generate consistent pastel colors from strings.

### 4. Integration
- The container measures its width (using `UseResizeObserver` or similar) and passes it to `FlameGraph`.
- On click, triggers the `onChange` handler to open the code.
