# State Management

## Replay Store (`replaySlice.ts`)

Location: `src/frontend/src/features/Dashboard/store/slices/replaySlice.ts`

---

## Two Modes Overview

| Mode | Source | Seekbar | Speed Control | Recording |
|------|--------|---------|---------------|-----------|
| **Live** | AI streaming | ❌ No | ❌ No | ✅ Auto-record |
| **Playback** | Saved session | ✅ Yes | ✅ Yes | ❌ Already saved |

---

### State Shape

```typescript
interface ReplayState {
  // Mode
  mode: 'idle' | 'live' | 'playback';
  
  // === LIVE MODE STATE ===
  isStreaming: boolean;         // AI is actively sending
  streamBuffer: ReplayAction[]; // Queue of incoming actions
  streamStartTime: number;      // When stream started (for recording)
  
  // === PLAYBACK MODE STATE ===
  currentTime: number;          // Current position (ms)
  totalDuration: number;        // Total duration (ms)
  playbackSpeed: 1 | 1.5 | 2;
  
  // === SHARED STATE ===
  isPlaying: boolean;           // Playing or paused
  isPaused: boolean;            // User paused (live or playback)
  actionQueue: ReplayAction[];  // All actions (grows in live, fixed in playback)
  currentActionIndex: number;   // Which action is active
  executedActionIds: Set<string>; // Track what's been executed
  
  // Thinking stream
  thoughts: ThoughtItem[];
  currentExplanation: string;
  
  // UI
  isPanelOpen: boolean;
  isUserInteracting: boolean;   // User is manually panning canvas
}

interface ThoughtItem {
  id: string;
  text: string;
  timestamp: number;
}
```

---

### Actions

```typescript
interface ReplayActions {
  // === MODE CONTROL ===
  startLiveStream: (sessionId: string) => void;
  endLiveStream: () => void;
  startPlayback: (session: ReplaySession) => void;
  reset: () => void;
  
  // === LIVE MODE ===
  // Called as AI sends chunks
  pushStreamAction: (action: ReplayAction) => void;
  executeNextBufferedAction: () => void;
  
  // === PLAYBACK MODE ===
  play: () => void;
  pause: () => void;
  seekTo: (time: number) => void;
  setSpeed: (speed: 1 | 1.5 | 2) => void;
  
  // === SHARED ===
  executeAction: (action: ReplayAction) => void;
  
  // Thinking
  appendThought: (text: string) => void;
  setExplanation: (text: string) => void;
  clearThoughts: () => void;
  
  // Panel
  togglePanel: () => void;
  setUserInteracting: (value: boolean) => void;
}
```

---

### Implementation

```typescript
// replaySlice.ts
import type { StateCreator } from 'zustand';

export const createReplaySlice: StateCreator<ReplaySlice> = (set, get) => ({
  // Initial state
  mode: 'idle',
  isStreaming: false,
  streamBuffer: [],
  streamStartTime: 0,
  
  currentTime: 0,
  totalDuration: 0,
  playbackSpeed: 1,
  
  isPlaying: false,
  isPaused: false,
  actionQueue: [],
  currentActionIndex: -1,
  executedActionIds: new Set(),
  
  thoughts: [],
  currentExplanation: '',
  isPanelOpen: false,
  isUserInteracting: false,

  // ========== LIVE MODE ==========
  
  startLiveStream: (sessionId) => set({
    mode: 'live',
    isStreaming: true,
    isPlaying: true,
    streamStartTime: Date.now(),
    actionQueue: [],
    currentActionIndex: -1,
    thoughts: [],
    isPanelOpen: true,
  }),

  endLiveStream: () => set((state) => ({
    isStreaming: false,
    // Calculate total duration from actions
    totalDuration: state.actionQueue.length > 0
      ? Math.max(...state.actionQueue.map(a => a.timestamp + a.duration))
      : 0,
  })),

  pushStreamAction: (action) => set((state) => ({
    streamBuffer: [...state.streamBuffer, action],
    actionQueue: [...state.actionQueue, action],
  })),

  executeNextBufferedAction: () => {
    const { streamBuffer, executedActionIds } = get();
    const nextAction = streamBuffer.find(a => !executedActionIds.has(a.id));
    
    if (nextAction) {
      get().executeAction(nextAction);
      set((state) => ({
        executedActionIds: new Set([...state.executedActionIds, nextAction.id]),
        currentActionIndex: state.actionQueue.findIndex(a => a.id === nextAction.id),
      }));
    }
  },

  // ========== PLAYBACK MODE ==========
  
  startPlayback: (session) => set({
    mode: 'playback',
    isPlaying: false,  // Start paused, user clicks play
    actionQueue: session.actionQueue,
    thoughts: session.thoughts,
    totalDuration: session.duration,
    currentTime: 0,
    currentActionIndex: 0,
    isPanelOpen: true,
  }),

  play: () => set({ isPlaying: true, isPaused: false }),
  
  pause: () => set({ isPlaying: false, isPaused: true }),
  
  seekTo: (time) => {
    const { actionQueue } = get();
    // Find the action at this time
    const index = actionQueue.findIndex(
      a => a.timestamp <= time && a.timestamp + a.duration > time
    );
    set({ 
      currentTime: time, 
      currentActionIndex: index >= 0 ? index : 0,
    });
  },

  setSpeed: (speed) => set({ playbackSpeed: speed }),

  // ========== SHARED ==========
  
  executeAction: (action) => {
    // This triggers the actual canvas/UI changes
    // Dispatched to canvas via subscription or useEffect
    if (action.explanation) {
      set({ currentExplanation: action.explanation });
    }
    if (action.thought) {
      get().appendThought(action.thought);
    }
  },

  reset: () => set({
    mode: 'idle',
    isStreaming: false,
    streamBuffer: [],
    isPlaying: false,
    isPaused: false,
    actionQueue: [],
    currentActionIndex: -1,
    currentTime: 0,
    totalDuration: 0,
    thoughts: [],
    currentExplanation: '',
    isPanelOpen: false,
    executedActionIds: new Set(),
  }),

  appendThought: (text) => set((state) => ({
    thoughts: [...state.thoughts, {
      id: crypto.randomUUID(),
      text,
      timestamp: Date.now(),
    }]
  })),

  setExplanation: (text) => set({ currentExplanation: text }),
  
  clearThoughts: () => set({ thoughts: [] }),
  
  togglePanel: () => set((state) => ({ isPanelOpen: !state.isPanelOpen })),
  
  setUserInteracting: (value) => set({ isUserInteracting: value }),
});
```

---

## Live Stream Engine Hook

Handles executing actions as they stream in:

```typescript
// hooks/useLiveStreamEngine.ts

export function useLiveStreamEngine() {
  const mode = useReplayStore(s => s.mode);
  const isStreaming = useReplayStore(s => s.isStreaming);
  const streamBuffer = useReplayStore(s => s.streamBuffer);
  const isPaused = useReplayStore(s => s.isPaused);
  const executeNextBufferedAction = useReplayStore(s => s.executeNextBufferedAction);

  // Process buffered actions
  useEffect(() => {
    if (mode !== 'live' || isPaused) return;
    
    // Small delay between actions for visual processing
    const timer = setInterval(() => {
      executeNextBufferedAction();
    }, 100);

    return () => clearInterval(timer);
  }, [mode, isPaused, streamBuffer.length]);
}
```

---

## Playback Engine Hook

Advances through timeline based on time:

```typescript
// hooks/usePlaybackEngine.ts

export function usePlaybackEngine() {
  const mode = useReplayStore(s => s.mode);
  const isPlaying = useReplayStore(s => s.isPlaying);
  const playbackSpeed = useReplayStore(s => s.playbackSpeed);
  const currentTime = useReplayStore(s => s.currentTime);
  const actionQueue = useReplayStore(s => s.actionQueue);
  const currentActionIndex = useReplayStore(s => s.currentActionIndex);

  const lastFrameRef = useRef<number>(0);

  useEffect(() => {
    if (mode !== 'playback' || !isPlaying) return;

    let animationId: number;

    const tick = (now: number) => {
      const delta = (now - lastFrameRef.current) * playbackSpeed;
      lastFrameRef.current = now;

      const newTime = currentTime + delta;
      
      // Find which action should be active at newTime
      const newIndex = actionQueue.findIndex(
        a => a.timestamp <= newTime && a.timestamp + a.duration > newTime
      );

      if (newIndex !== currentActionIndex && newIndex >= 0) {
        // Execute the new action
        useReplayStore.getState().executeAction(actionQueue[newIndex]);
      }

      useReplayStore.setState({ 
        currentTime: newTime,
        currentActionIndex: newIndex >= 0 ? newIndex : currentActionIndex,
      });

      animationId = requestAnimationFrame(tick);
    };

    lastFrameRef.current = performance.now();
    animationId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(animationId);
  }, [mode, isPlaying, playbackSpeed]);
}
```

---

## History Store (`historySlice.ts`)

Location: `src/frontend/src/features/Dashboard/store/slices/historySlice.ts`

### Purpose

Persist replay sessions so users can:
- Review past walkthroughs
- Resume interrupted sessions
- Share replays with teammates

### State Shape

```typescript
interface ReplaySession {
  id: string;
  projectId: string;
  title: string;               // User's original query
  createdAt: number;
  duration: number;
  actionQueue: ReplayAction[];
  thoughts: ThoughtItem[];
  bookmarks: Bookmark[];       // User-marked moments
}

interface Bookmark {
  id: string;
  timestamp: number;
  label: string;
  nodeKey?: string;
}

interface HistoryState {
  sessions: Record<string, ReplaySession>;
  currentSessionId: string | null;
}

interface HistoryActions {
  createSession: (projectId: string, title: string) => string;
  saveSession: (session: ReplaySession) => void;
  loadSession: (sessionId: string) => ReplaySession | null;
  deleteSession: (sessionId: string) => void;
  
  addBookmark: (sessionId: string, bookmark: Omit<Bookmark, 'id'>) => void;
  removeBookmark: (sessionId: string, bookmarkId: string) => void;
}
```

### Persistence Strategy

| Option | Pros | Cons |
|--------|------|------|
| **LocalStorage** | Simple, no backend | 5MB limit, single device |
| **IndexedDB** | Large storage, structured | Complex API |
| **Server-side** | Cross-device, shareable | Requires backend work |

**Recommendation**: Start with **IndexedDB** via a wrapper like `idb-keyval`:
- Supports large action queues
- Works offline
- Can migrate to server later

```typescript
// Simple IndexedDB wrapper
import { get, set, del } from 'idb-keyval';

const saveSession = async (session: ReplaySession) => {
  await set(`replay-${session.id}`, session);
};

const loadSession = async (id: string) => {
  return await get(`replay-${id}`);
};
```
