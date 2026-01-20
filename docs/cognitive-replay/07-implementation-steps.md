# Implementation Steps

## Phase 1: Foundation (Types & Store)

**Goal**: Core data structures and state management with Live/Playback modes.

### Step 1.1: Create Types
- [ ] Create `src/frontend/src/types/replay.ts`
- [ ] Define `ReplayAction` union type
- [ ] Define `ThoughtItem`, `Bookmark` interfaces
- [ ] Define mode types (`idle`, `live`, `playback`)

### Step 1.2: Create Replay Store
- [ ] Create `store/slices/replaySlice.ts`
- [ ] Implement mode switching (`idle` → `live` → `playback`)
- [ ] Implement Live mode state (streaming, buffer)
- [ ] Implement Playback mode state (seek, speed)
- [ ] Add to `useProjectStore`

### Step 1.3: Create History Store
- [ ] Install `idb` package
- [ ] Create `lib/replayDB.ts` for IndexedDB
- [ ] Create `store/slices/historySlice.ts`

---

## Phase 2: Command Bar UI

**Goal**: User control interface with mode-specific controls.

### Step 2.1: Create Component Structure
- [ ] Create `components/Replay/CommandBar/CommandBar.tsx`
- [ ] Create `components/Replay/CommandBar/CommandInput.tsx`
- [ ] Create `components/Replay/CommandBar/LiveControls.tsx`
- [ ] Create `components/Replay/CommandBar/PlaybackControls.tsx`

### Step 2.2: Implement Live Mode Controls
- [ ] Pause/Resume button
- [ ] 🔴 LIVE streaming indicator
- [ ] Progress bar (no seeking)
- [ ] Elapsed time display

### Step 2.3: Implement Playback Mode Controls
- [ ] Play/Pause button
- [ ] Seekbar (range input)
- [ ] Time display (current / total)
- [ ] Speed selector (1x, 1.5x, 2x)
- [ ] Action markers on timeline

### Step 2.4: Style & Polish
- [ ] Glassmorphism background
- [ ] Smooth transitions between states
- [ ] Keyboard shortcuts (Space, arrows)

---

## Phase 3: Thinking Panel

**Goal**: AI thought stream display.

### Step 3.1: Create Panel Structure
- [ ] Create `components/Replay/ThinkingPanel/ThinkingPanel.tsx`
- [ ] Create `components/Replay/ThinkingPanel/ThoughtStream.tsx`
- [ ] Create `components/Replay/ThinkingPanel/ExplanationCard.tsx`

### Step 3.2: Implement Streaming Animation
- [ ] Create `useStreamingText` hook
- [ ] Add fade-in for new thoughts
- [ ] Auto-scroll to newest thought

### Step 3.3: Panel Transitions
- [ ] Slide-in/out animation
- [ ] Close button
- [ ] Responsive width

---

## Phase 4: Canvas Integration

**Goal**: Visual actions on the node graph.

### Step 4.1: Canvas Navigator Hook
- [ ] Create `hooks/useCanvasNavigator.ts`
- [ ] Implement `panToNode` function
- [ ] Implement `fitToNodes` function

### Step 4.2: Modify CanvasView
- [ ] Import replay store
- [ ] Listen for current action changes
- [ ] Execute FOCUS/EXPAND/SELECT actions
- [ ] Handle user interaction (pause auto-panning)

### Step 4.3: Node Highlighting
- [ ] Modify `EnhancedNode.tsx` for line highlights
- [ ] Add focus ring animation for active node
- [ ] Style highlight colors (orange, blue, green)

---

## Phase 5: Replay Engines

**Goal**: Orchestrate timeline execution for both modes.

### Step 5.1: Live Stream Engine
- [ ] Create `hooks/useLiveStreamEngine.ts`
- [ ] Process actions as they arrive from AI
- [ ] Handle pause/resume during streaming
- [ ] Auto-record to history

### Step 5.2: Playback Engine
- [ ] Create `hooks/usePlaybackEngine.ts`
- [ ] Implement `requestAnimationFrame` time tracking
- [ ] Handle seek to arbitrary position
- [ ] Handle speed changes

### Step 5.3: Testing with Mock Data
- [ ] Create sample action queue
- [ ] Test Live mode with simulated streaming
- [ ] Test Playback mode with full timeline
- [ ] Verify seek functionality

---

## Phase 6: Integration & Polish

### Step 6.1: Mount Components
- [ ] Add CommandBar to Dashboard.tsx
- [ ] Add ThinkingPanel to Dashboard.tsx
- [ ] Connect to replay store

### Step 6.2: History UI
- [ ] Add history list to Sidebar
- [ ] Implement session load/delete
- [ ] Show bookmarks in timeline

### Step 6.3: Polish
- [ ] Keyboard shortcut hints
- [ ] Error states
- [ ] Loading states

---

## Verification Checklist

### Live Stream Mode
- [ ] Actions execute as AI streams them
- [ ] Pause stops action execution (AI keeps streaming)
- [ ] Progress bar shows elapsed time
- [ ] 🔴 LIVE indicator pulses
- [ ] Session auto-saves to history

### Playback Mode
- [ ] Play → actions execute at timestamps
- [ ] Pause → freezes, timer stops
- [ ] Seek → jumps to correct position
- [ ] Speed → 1x/1.5x/2x affects timing
- [ ] Can load any saved session

### Canvas
- [ ] Canvas smoothly pans to focused node
- [ ] Nodes expand/collapse properly
- [ ] Lines highlight in correct color
- [ ] User can still manually pan/zoom
- [ ] Manual interaction pauses auto-panning

### Thinking Panel
- [ ] Slides in when replay starts
- [ ] Thoughts stream character-by-character
- [ ] Explanation updates per action
- [ ] Close button works

### History
- [ ] Sessions save to IndexedDB
- [ ] Session list loads for project
- [ ] Can resume a saved session
- [ ] Bookmarks persist

---

## Estimated Effort

| Phase | Complexity | Est. Time |
|-------|------------|-----------|
| Phase 1 | Medium | 3-4 hours |
| Phase 2 | Medium | 4-5 hours |
| Phase 3 | Medium | 2-3 hours |
| Phase 4 | High | 4-5 hours |
| Phase 5 | High | 4-5 hours |
| Phase 6 | Medium | 3-4 hours |
| **Total** | | **20-26 hours** |
