# UI Components

## Component Structure

```
src/frontend/src/features/Dashboard/components/Replay/
├── CommandBar/
│   ├── CommandBar.tsx        # Container
│   ├── CommandInput.tsx      # Text input
│   ├── PlaybackControls.tsx  # Play/pause/seek (Playback mode)
│   ├── LiveControls.tsx      # Pause/streaming indicator (Live mode)
│   └── TimelineMarkers.tsx   # Action dots on seekbar
├── ThinkingPanel/
│   ├── ThinkingPanel.tsx     # Container
│   ├── ThoughtStream.tsx     # Scrolling thoughts
│   └── ExplanationCard.tsx   # Current explanation
└── index.ts
```

---

## Command Bar

**Location**: Bottom center, above all content

### Mode-Specific UI

#### Idle Mode
```
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │  💬 Ask AI about this code...                                        │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Live Stream Mode (AI is generating)
```
┌──────────────────────────────────────────────────────────────────────────┐
│  ❚❚   ●────────────────────────────────→   🔴 LIVE   00:45              │
│       ↑                                                                  │
│  Progress bar (no seeking - can't jump to future)                        │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │  Streaming...                                                     ⏸  │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Live Mode Controls:**
- ❚❚ Pause button (pauses action execution, AI keeps streaming)
- 🔴 LIVE indicator (pulsing dot)
- No seekbar (can't seek into the future)
- Timer shows elapsed time

#### Playback Mode (Saved session)
```
┌──────────────────────────────────────────────────────────────────────────┐
│ ▶  ❚❚   ←──────●─────|──────|────────→   01:15 / 03:45      [1.5x ▼]    │
│                      ↑      ↑                                            │
│              action markers on seekbar                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │  💬 Ask follow-up question...                                        │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Playback Mode Controls:**
- ▶ Play button
- ❚❚ Pause button
- Full seekbar (drag to any position)
- Time display (current / total)
- Speed selector (1x, 1.5x, 2x)
- Action markers show key moments

---

### States Summary

| State | Controls | Input | Indicator |
|-------|----------|-------|-----------|
| **Idle** | Hidden | Enabled, focused | None |
| **Loading** | Hidden | Disabled | "Thinking..." |
| **Live Streaming** | Pause only | Disabled | 🔴 LIVE |
| **Live Paused** | Resume only | Enabled | ⏸ Paused |
| **Playback** | Full controls | Enabled | Time / Speed |
| **Playback Paused** | Full controls | Enabled | ⏸ + Time |

---

### CSS

```css
.command-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: min(800px, 90vw);
  
  /* Glassmorphism */
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  
  padding: 16px;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
}

.live-dot {
  width: 10px;
  height: 10px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.seekbar {
  appearance: none;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  cursor: pointer;
}

.seekbar::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: grab;
}

.progress-bar {
  /* Live mode - no interaction */
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.progress-bar .fill {
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  height: 100%;
  border-radius: 2px;
  transition: width 0.1s linear;
}
```

### Component Props

```typescript
interface CommandBarProps {
  onSubmit: (query: string) => void;
}

interface LiveControlsProps {
  isPaused: boolean;
  elapsedTime: number;
  onPause: () => void;
  onResume: () => void;
}

interface PlaybackControlsProps {
  isPlaying: boolean;
  currentTime: number;
  totalDuration: number;
  speed: 1 | 1.5 | 2;
  actions: ReplayAction[];  // For markers
  onPlay: () => void;
  onPause: () => void;
  onSeek: (time: number) => void;
  onSpeedChange: (speed: 1 | 1.5 | 2) => void;
}
```

---

## Thinking Panel

**Location**: Right side, slides in during replay

### Visual Design

```
┌─────────────────────────────┐
│ ✧ AI COGNITIVE REPLAY    ✕ │
├─────────────────────────────┤
│ THOUGHT STREAM              │ ← Faded label
│ ┌─────────────────────────┐ │
│ │ Analyzing dependencies..│ │
│ │ Identifying entry point.│ │
│ │ Focus on 'create_child'.│ │ ← Newest at bottom
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ EXPLANATION                 │
│ ┌─────────────────────────┐ │
│ │ The 'create_child'      │ │
│ │ function is called by   │ │ ← Main narration
│ │ 'main'. It initializes  │ │
│ │ a new 'Child' instance. │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ Ask follow-up...     ↵  │ │ ← Optional mini input
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### CSS

```css
.thinking-panel {
  position: fixed;
  top: 64px;
  right: 0;
  width: 360px;
  height: calc(100vh - 128px);
  
  /* Glassmorphism */
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(16px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  
  /* Slide animation */
  transform: translateX(100%);
  transition: transform 0.3s ease-out;
}

.thinking-panel.open {
  transform: translateX(0);
}

.thought-item {
  opacity: 0;
  animation: fadeIn 0.3s forwards;
}

@keyframes fadeIn {
  to { opacity: 0.7; }
}
```

### Streaming Text Hook

```typescript
function useStreamingText(text: string, speed = 30) {
  const [displayed, setDisplayed] = useState('');
  
  useEffect(() => {
    if (!text) return;
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, ++i));
      } else {
        clearInterval(timer);
      }
    }, speed);
    return () => clearInterval(timer);
  }, [text, speed]);
  
  return displayed;
}
```

### Component Props

```typescript
interface ThinkingPanelProps {
  isOpen: boolean;
  thoughts: ThoughtItem[];
  explanation: string;
  onClose: () => void;
}
```
