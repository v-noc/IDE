# History & Persistence

## Purpose

Store replay sessions so users can:
- Resume interrupted walkthroughs
- Review past explanations
- Bookmark key moments
- Share replays (future)

---

## Storage Strategy

### Option Comparison

| Option | Capacity | Offline | Sync | Complexity |
|--------|----------|---------|------|------------|
| LocalStorage | 5MB | ✅ | ❌ | Low |
| **IndexedDB** | 100MB+ | ✅ | ❌ | Medium |
| Server (ArangoDB) | ∞ | ❌ | ✅ | High |

**Recommendation**: Start with **IndexedDB** for MVP:
- Large enough for many sessions
- Works offline
- Can sync to server later

---

## Data Schema

```typescript
// types/replay-history.ts

interface ReplaySession {
  id: string;                    // UUID
  projectId: string;             // Project this belongs to
  title: string;                 // User's query
  createdAt: number;             // Timestamp
  updatedAt: number;             // Last modified
  duration: number;              // Total ms
  status: 'in_progress' | 'completed' | 'abandoned';
  
  // The actual content
  actionQueue: ReplayAction[];
  thoughts: ThoughtItem[];
  
  // User additions
  bookmarks: Bookmark[];
  notes?: string;
}

interface Bookmark {
  id: string;
  timestamp: number;             // Position in replay
  label: string;                 // User label
  nodeKey?: string;              // Optional node reference
}

interface ReplayHistoryIndex {
  id: string;
  projectId: string;
  title: string;
  createdAt: number;
  duration: number;
  status: string;
  // Lightweight for list views
}
```

---

## IndexedDB Implementation

Using `idb` library for cleaner API:

```typescript
// lib/replayDB.ts
import { openDB, type DBSchema } from 'idb';

interface ReplayDBSchema extends DBSchema {
  sessions: {
    key: string;
    value: ReplaySession;
    indexes: {
      'by-project': string;
      'by-date': number;
    };
  };
}

const DB_NAME = 'vnoc-replay';
const DB_VERSION = 1;

async function getDB() {
  return openDB<ReplayDBSchema>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      const store = db.createObjectStore('sessions', { keyPath: 'id' });
      store.createIndex('by-project', 'projectId');
      store.createIndex('by-date', 'createdAt');
    },
  });
}

export const replayDB = {
  async save(session: ReplaySession) {
    const db = await getDB();
    await db.put('sessions', { ...session, updatedAt: Date.now() });
  },

  async get(id: string) {
    const db = await getDB();
    return db.get('sessions', id);
  },

  async listByProject(projectId: string): Promise<ReplayHistoryIndex[]> {
    const db = await getDB();
    const sessions = await db.getAllFromIndex('sessions', 'by-project', projectId);
    return sessions.map(s => ({
      id: s.id,
      projectId: s.projectId,
      title: s.title,
      createdAt: s.createdAt,
      duration: s.duration,
      status: s.status,
    }));
  },

  async delete(id: string) {
    const db = await getDB();
    await db.delete('sessions', id);
  },

  async clear() {
    const db = await getDB();
    await db.clear('sessions');
  },
};
```

---

## History Store (Zustand)

```typescript
// store/slices/historySlice.ts
import { replayDB } from '@/lib/replayDB';

interface HistorySlice {
  // State (in-memory cache)
  sessionIndex: ReplayHistoryIndex[];
  currentSessionId: string | null;
  
  // Actions
  loadProjectHistory: (projectId: string) => Promise<void>;
  createSession: (projectId: string, title: string) => Promise<string>;
  saveCurrentSession: () => Promise<void>;
  loadSession: (id: string) => Promise<ReplaySession | null>;
  deleteSession: (id: string) => Promise<void>;
  
  // Bookmarks
  addBookmark: (label: string, timestamp?: number) => void;
  removeBookmark: (bookmarkId: string) => void;
}

export const createHistorySlice: StateCreator<HistorySlice> = (set, get) => ({
  sessionIndex: [],
  currentSessionId: null,

  loadProjectHistory: async (projectId) => {
    const index = await replayDB.listByProject(projectId);
    set({ sessionIndex: index.sort((a, b) => b.createdAt - a.createdAt) });
  },

  createSession: async (projectId, title) => {
    const session: ReplaySession = {
      id: crypto.randomUUID(),
      projectId,
      title,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      duration: 0,
      status: 'in_progress',
      actionQueue: [],
      thoughts: [],
      bookmarks: [],
    };
    await replayDB.save(session);
    set({ currentSessionId: session.id });
    return session.id;
  },

  saveCurrentSession: async () => {
    const { currentSessionId } = get();
    if (!currentSessionId) return;
    
    const replayState = useReplayStore.getState();
    const existing = await replayDB.get(currentSessionId);
    if (!existing) return;
    
    await replayDB.save({
      ...existing,
      actionQueue: replayState.actionQueue,
      thoughts: replayState.thoughts,
      duration: replayState.totalDuration,
      status: replayState.currentActionIndex >= replayState.actionQueue.length - 1
        ? 'completed'
        : 'in_progress',
    });
  },
});
```

---

## UI Integration

### History Panel (in Sidebar)

```
┌─────────────────────────────┐
│ 📜 REPLAY HISTORY           │
├─────────────────────────────┤
│ Today                       │
│ ┌─────────────────────────┐ │
│ │ "Walk me through Child" │ │
│ │ 3:45 • 2 bookmarks      │ │
│ └─────────────────────────┘ │
│                             │
│ Yesterday                   │
│ ┌─────────────────────────┐ │
│ │ "Explain init flow"     │ │
│ │ 5:12 • Completed ✓      │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### Auto-Save Trigger

```typescript
// In CommandBar or ReplayEngine
useEffect(() => {
  if (!isPlaying) return;
  
  // Save every 30 seconds
  const interval = setInterval(() => {
    saveCurrentSession();
  }, 30000);
  
  return () => clearInterval(interval);
}, [isPlaying]);

// Also save on pause/stop
useEffect(() => {
  if (!isPlaying && currentSessionId) {
    saveCurrentSession();
  }
}, [isPlaying]);
```

---

## Future: Server Sync

When ready to add server persistence:

```typescript
// Sync on save
async function syncToServer(session: ReplaySession) {
  await fetch(`/api/replays/${session.id}`, {
    method: 'PUT',
    body: JSON.stringify(session),
  });
}

// Pull on load
async function syncFromServer(projectId: string) {
  const response = await fetch(`/api/projects/${projectId}/replays`);
  const sessions = await response.json();
  for (const s of sessions) {
    await replayDB.save(s);
  }
}
```
