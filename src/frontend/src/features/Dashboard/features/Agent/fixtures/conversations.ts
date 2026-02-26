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
  {
    id: "chat-4",
    title: "Node spotlight demo",
    date: "Feb 26, 2026",
    duration: "3 min",
    messages: [
      {
        id: "chat-4-assistant-1",
        role: "assistant",
        parts: [
          {
            type: "text",
            text: "File node highlight: `main` (node_type: file). ID: FileSchema/372f9c6e-7ea2-44ed-9678-b56a0ca8c3f1.",
          },
          {
            type: "event",
            event: {
              at: 0,
              type: "focus",
              payload: {
                nodeId: "FileSchema/372f9c6e-7ea2-44ed-9678-b56a0ca8c3f1",
              },
            },
          },
        ],
      },
      {
        id: "chat-4-assistant-2",
        role: "assistant",
        parts: [
          {
            type: "text",
            text: "Call node highlight: `main` (node_type: call). ID: CallSchema/9a1dc48d-1099-4fcb-8610-d266765bf6f8. Target function: FunctionSchema/11b1c19e-faa5-44f1-836a-c1ef80d43c87.",
          },
          {
            type: "event",
            event: {
              at: 1200,
              type: "focus",
              payload: {
                nodeId: "CallSchema/9a1dc48d-1099-4fcb-8610-d266765bf6f8",
              },
            },
          },
        ],
      },
      {
        id: "chat-4-assistant-3",
        role: "assistant",
        parts: [
          {
            type: "text",
            text: "Function node highlight: `runner` (node_type: function). ID: FunctionSchema/fb04a14a-2746-4212-8bdd-cb70779c416c. qname: sample_project.main.runner.",
          },
          {
            type: "event",
            event: {
              at: 2400,
              type: "focus",
              payload: {
                nodeId: "FunctionSchema/fb04a14a-2746-4212-8bdd-cb70779c416c",
              },
            },
          },
        ],
      },
    ],
  },
];
