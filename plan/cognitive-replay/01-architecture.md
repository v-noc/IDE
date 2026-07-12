# Architecture & Data Flow

## Current V-NOC Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **State** | Zustand + Immer | Tab-scoped state via slices |
| **Canvas** | ReactFlow | Node graph via `CanvasView.tsx` |
| **Stores** | `useProjectStore`, `useTabStore` | Selection, focus, UI state |

---

## Two Operating Modes

> [!IMPORTANT]
> The replay system has **two distinct modes** that share the same visual behavior but differ in how actions are received.

### Mode 1: Live Stream (Real-time AI)

Actions execute **as they arrive** from the AI, like a live video stream:

```
User asks question
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                    AI STREAMING RESPONSE                      │
│                                                               │
│   ──────────────────────────────────────────────►  time       │
│   │         │         │         │         │                   │
│   ▼         ▼         ▼         ▼         ▼                   │
│ action1  action2  action3  action4  action5  ...              │
│   │         │         │         │         │                   │
│   ▼         ▼         ▼         ▼         ▼                   │
│ EXECUTE  EXECUTE  EXECUTE  EXECUTE  EXECUTE                   │
│  NOW      NOW      NOW      NOW      NOW                      │
└──────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Actions execute immediately as AI sends them
- No seekbar (can't seek into the future)
- Shows "streaming" indicator
- User can pause, but can't rewind (yet)
- Session is recorded for later playback

### Mode 2: Playback (On-Demand)

User plays a **saved session** like a video:

```
┌──────────────────────────────────────────────────────────────┐
│                    SAVED SESSION                              │
│                                                               │
│   [action1][action2][action3][action4][action5]               │
│       │                                                       │
│       ├───── Full timeline known upfront                      │
│       │                                                       │
│   ──●────────────────────────────────────►  seekbar           │
│    ↑                                                          │
│    └── User can seek to any position                          │
└──────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Full timeline loaded from history
- Seekbar allows jumping to any point
- Play/pause works like a video
- Speed control (1x, 1.5x, 2x)
- Can loop or restart

---

## Data Flow: Live Stream Mode

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                │
│            "Walk me through how Child is initialized"            │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (WebSocket/SSE)                    │
│                                                                  │
│  Streams chunks:                                                 │
│    { type: "thought", text: "Analyzing..." }                    │
│    { type: "action", action: { type: "FOCUS", nodeKey: "x" } }  │
│    { type: "action", action: { type: "EXPAND", nodeKey: "x" } } │
│    { type: "thought", text: "Following call..." }               │
│    ...                                                           │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────┐
            │                             │                     │
            ▼                             ▼                     ▼
   ┌───────────────┐            ┌───────────────┐    ┌───────────────┐
   │THINKING PANEL │            │ REPLAY STORE  │    │ HISTORY STORE │
   │               │            │               │    │               │
   │ Append thought│            │ Queue action  │    │ Record action │
   │ immediately   │            │ Execute next  │    │ for playback  │
   └───────────────┘            └───────┬───────┘    └───────────────┘
                                        │
                                        ▼ (execute immediately)
                                ┌───────────────┐
                                │    CANVAS     │
                                │               │
                                │ • Pan/zoom    │
                                │ • Expand node │
                                │ • Highlight   │
                                └───────────────┘
```

## Data Flow: Playback Mode

```
┌─────────────────────────────────────────────────────────────────┐
│                       HISTORY STORE                              │
│                                                                  │
│   Load session by ID                                             │
│   → Full actionQueue[]                                           │
│   → All thoughts[]                                               │
│   → Known totalDuration                                          │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       REPLAY STORE                               │
│                                                                  │
│   mode: 'playback'                                               │
│   actionQueue: [...loaded actions...]                           │
│   currentTime: 0                                                 │
│   totalDuration: 45000                                           │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                    ▲                     │                     ▲
                    │                     ▼                     │
           ┌────────┴──────┐    ┌───────────────┐    ┌─────────┴─────┐
           │  SEEKBAR      │    │ACTION ENGINE  │    │ PLAY/PAUSE    │
           │               │    │               │    │               │
           │ User drags to │    │ requestAnim   │    │ Toggle state  │
           │ any position  │    │ Frame loop    │    │               │
           └───────────────┘    └───────┬───────┘    └───────────────┘
                                        │
                                        ▼ (execute at timestamp)
                                ┌───────────────┐
                                │    CANVAS     │
                                │               │
                                │ • Pan/zoom    │
                                │ • Expand node │
                                │ • Highlight   │
                                └───────────────┘
```

---

## Store Relationships

```typescript
// Existing stores (unchanged)
useProjectStore    // Selection, focus, node expansion
useTabStore        // Tab management

// New stores
useReplayStore     // Playback state, action queue, mode
useHistoryStore    // Session persistence, bookmarks
```

### Mode State

```typescript
interface ReplayState {
  mode: 'idle' | 'live' | 'playback';
  
  // Live mode specific
  isStreaming: boolean;
  streamBuffer: ReplayAction[];  // Actions waiting to execute
  
  // Playback mode specific  
  currentTime: number;
  totalDuration: number;
  playbackSpeed: 1 | 1.5 | 2;
  
  // Shared
  isPlaying: boolean;
  actionQueue: ReplayAction[];
  currentActionIndex: number;
}
```
