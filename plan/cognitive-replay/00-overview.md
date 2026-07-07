# Cognitive Replay UI - Overview

> Transform V-NOC into a cinematic "Cognitive Replay" platform where AI-driven code walkthroughs feel like watching a video.

## Vision

Instead of scrolling chat, the AI **controls the canvas** like a video:
- Canvas pans/zooms smoothly between nodes
- Code nodes expand/collapse with animations
- Specific lines glow as the AI explains them
- A timeline with play/pause/seek controls

## Two Operating Modes

| Mode | When | Controls | Purpose |
|------|------|----------|---------|
| **Live Stream** | User asks a question | Pause only | Real-time AI walkthrough |
| **Playback** | User loads saved session | Full controls | Review past walkthroughs |

## Document Index

| File | Domain |
|------|--------|
| [01-architecture.md](01-architecture.md) | System architecture & data flow |
| [02-state-management.md](02-state-management.md) | Replay store & slices |
| [03-action-schema.md](03-action-schema.md) | AI-to-UI action language |
| [04-ui-components.md](04-ui-components.md) | Command bar, thinking panel |
| [05-canvas-integration.md](05-canvas-integration.md) | Canvas pan/zoom, highlights |
| [06-history-persistence.md](06-history-persistence.md) | Storing replay sessions |
| [07-implementation-steps.md](07-implementation-steps.md) | Phased build order |

## Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                         CANVAS                                   │
│    ┌──────────┐         ┌──────────┐         ┌──────────┐       │
│    │   main   │ ─────── │ create_  │ ─────── │  Child   │       │
│    └──────────┘         └────┬─────┘         └──────────┘       │
│                         ╔════╧════╗                              │
│                         ║ FOCUSED ║  ◄── Active node             │
│                         ╚═════════╝                              │
├─────────────────────────────────────────────────────────────────┤
│  ▶ ❚❚ ──●─────────────────────── 01:15 / 03:45   [Thinking...]  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Ask AI about this code...                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Decisions Needed

1. **Panel Position**: Right side (like mockup) or left side?
2. **History Storage**: IndexedDB (recommended) or server-side?
3. **Initial Scope**: Mock timeline first or real AI from start?
