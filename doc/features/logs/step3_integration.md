# Step 3: Integration and Code Toggling

## Goal
Integrate the Flame Chart into the Logs container and enable switching between views. Also implement the "Click to View Code" feature.

## Changes

### 1. Update Logs Container
**File:** `src/frontend/src/features/Dashboard/features/Main/components/Sandbox/features/Logs/index.tsx`
- Add State: `viewMode` ('list' | 'flame').
- Add UI Control: A toggle button group in the header (Icons for List vs Chart).
- Conditional Rendering:
    - If `list`: Render existing `logs.map(...)`.
    - If `flame`: Render `<FlameChart nodes={logs} />`.

### 2. Connect to Code View
- The `LogsContainer` component or `FlameChart` needs to communicate with the `Code` component.
- **Mechanism**:
    - If the application uses a global selection state (e.g., Redux or Context), dispatch an action like `selectFunction(functionId)`.
    - Alternatively, check if `useEditableCode` or similar hooks expose a way to set the active file/function.
- **Action**:
    - When a flame bar is clicked, get its `function_id`.
    - Call the function to set the active code view to that `function_id`.

### 3. Final Polish
- Ensure animations match the "premium" feel (framer-motion for simple transitions).
- Verify dark mode compatibility.
