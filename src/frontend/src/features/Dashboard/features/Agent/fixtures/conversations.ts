import type { Conversation } from "../types/conversation";

export const conversationFixtures: Conversation[] = [
  {
    id: "chat-1",
    title: "Analyze dependency graph",
    date: "Feb 26, 2026",
    duration: "18 min",
    messages: [
      {
        id: "chat-1-user-1",
        role: "user",
        parts: [
          {
            type: "text",
            text: "Can you inspect the dependency graph for cyclic modules?",
          },
        ],
      },
      {
        id: "chat-1-assistant-1",
        role: "assistant",
        parts: [
          { type: "text", text: "I found two circular dependency clusters." },
          {
            type: "event",
            event: { at: 0, type: "focus", payload: { nodeId: "api/router" } },
          },
          {
            type: "event",
            event: { at: 1200, type: "click", payload: { nodeId: "utils/log" } },
          },
        ],
      },
    ],
  },
  {
    id: "chat-2",
    title: "Explain selected node changes",
    date: "Feb 25, 2026",
    duration: "1 hr 05 min",
    messages: [
      {
        id: "chat-2-user-1",
        role: "user",
        parts: [
          {
            type: "text",
            text: "Walk me through the selected node updates since last commit.",
          },
        ],
      },
      {
        id: "chat-2-assistant-1",
        role: "assistant",
        parts: [
          {
            type: "text",
            text: "The node had one interface rename and two dependency additions.",
          },
          {
            type: "event",
            event: { at: 0, type: "focus", payload: { nodeId: "services/auth" } },
          },
          {
            type: "event",
            event: { at: 850, type: "wait", payload: { ms: 1500 } },
          },
        ],
      },
    ],
  },
  {
    id: "chat-3",
    title: "Summarize version diff",
    date: "Feb 24, 2026",
    duration: "42 min",
    messages: [
      {
        id: "chat-3-user-1",
        role: "user",
        parts: [
          {
            type: "text",
            text: "Give me a concise summary for this version diff.",
          },
        ],
      },
      {
        id: "chat-3-assistant-1",
        role: "assistant",
        parts: [
          {
            type: "text",
            text: "This revision mostly removes dead paths and tightens typing.",
          },
          {
            type: "event",
            event: { at: 500, type: "click", payload: { nodeId: "hooks/useTree" } },
          },
        ],
      },
    ],
  },
];
