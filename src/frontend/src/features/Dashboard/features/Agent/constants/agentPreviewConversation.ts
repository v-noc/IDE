import type { Walkthrough } from "@/features/Dashboard/features/Agent/walkthrough/types/walkthrough";
import type { WireConversation } from "@/types/agent";

/** Local-only conversation id: skips REST hydration and socket room join. */
export const AGENT_UI_PREVIEW_CONVERSATION_ID = "__vnoc_agent_ui_preview__";

/** Example canvas node ids for the preview walkthrough (must exist in the loaded project tree). */
export const AGENT_PREVIEW_WALKTHROUGH_FILE_NODE_ID =
  "FileSchema/372f9c6e-7ea2-44ed-9678-b56a0ca8c3f1";
export const AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID =
  "FunctionSchema/11b1c19e-faa5-44f1-836a-c1ef80d43c87";

/**
 * Sample tour: file node, function node, then Monaco line highlights (lines 3–5 and line 4).
 * Line numbers assume a typical small function body (e.g. declaration on line 2, body from line 3).
 */
export const AGENT_PREVIEW_CANVAS_WALKTHROUGH: Walkthrough = {
  meta: {
    id: "preview-canvas-two-step",
    title: "Canvas quick tour",
    description:
      "Sample walkthrough: file, function, then inline code highlights with line-anchored popovers.",
    version: 2,
  },
  steps: [
    {
      id: "preview-step-file",
      actions: [
        {
          type: "pan-canvas",
          to: { nodeId: AGENT_PREVIEW_WALKTHROUGH_FILE_NODE_ID },
        },
        {
          type: "focus-node",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FILE_NODE_ID,
        },
      ],
      popover: {
        title: "File node",
        body: "This file sits in your project tree. Use the walkthrough bar on the Canvas tab to play or step through.",
        anchor: {
          type: "node",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FILE_NODE_ID,
        },
        side: "right",
      },
    },
    {
      id: "preview-step-function",
      actions: [
        { type: "clear-highlight" },
        {
          type: "pan-canvas",
          to: { nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID },
        },
        {
          type: "focus-node",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
        },
      ],
      popover: {
        title: "Function node",
        body: "This is the target function. Next we open its code and spotlight part of the body in the Monaco editor.",
        anchor: {
          type: "node",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
        },
        side: "right",
      },
    },
    {
      id: "preview-step-function-lines-3-5",
      actions: [
        { type: "clear-highlight" },
        {
          type: "focus-node",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
        },
        {
          type: "show-code",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
        },
        {
          type: "highlight-code",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
          lines: [{ from: 3, to: 5 }],
        },
      ],
      popover: {
        title: "Function body (lines 3–5)",
        body: "The walkthrough highlights the first lines of the function body. Monaco decorations mark the range; the amber frame tracks it while you scroll.",
        anchor: {
          type: "code-line",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
          line: 4,
        },
        side: "right",
      },
    },
    {
      id: "preview-step-function-line-4",
      actions: [
        { type: "clear-highlight" },
        {
          type: "highlight-code",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
          lines: [{ from: 4, to: 4 }],
        },
      ],
      popover: {
        title: "Line 4",
        body: "A narrower highlight on a single line. The popover anchor follows this line in the editor viewport.",
        anchor: {
          type: "code-line",
          nodeId: AGENT_PREVIEW_WALKTHROUGH_FUNCTION_NODE_ID,
          line: 4,
        },
        side: "right",
      },
    },
  ],
};

export function isAgentPreviewConversationId(id: string | null | undefined): boolean {
  return id === AGENT_UI_PREVIEW_CONVERSATION_ID;
}

/** Preview task parts use synthetic ids; skip real task HTTP calls. */
export function isAgentPreviewTaskId(taskId: string | null | undefined): boolean {
  return Boolean(taskId && taskId.startsWith("preview-"));
}

const SAMPLE_MARKDOWN = `## Markdown check

**Bold**, *italic*, and \`inline code\`.

### Lists
- First item
- Second item
- Third item

### Code

\`\`\`bash
sudo apt-get install markdown-editor
\`\`\`

\`\`\`python
print("Hello, World!")
\`\`\`

### Quote

> Short blockquote for styling.

---

Plain paragraph after a rule.
`;

export function createAgentUiPreviewWire(): WireConversation {
  const now = new Date().toISOString();
  return {
    id: AGENT_UI_PREVIEW_CONVERSATION_ID,
    title: "UI preview (sample)",
    description:
      "Local fixture: canvas walkthrough, markdown, and task layout",
    message_count: 4,
    has_active_task: true,
    created_at: now,
    updated_at: now,
    messages: [
      {
        id: "preview-user-1",
        role: "user",
        sequence: 0,
        parts: [
          {
            type: "text",
            text: "Show a canvas walkthrough, markdown formatting, and a task with sub-tasks.",
          },
        ],
        created_at: now,
      },
      {
        id: "preview-assistant-walkthrough",
        role: "assistant",
        sequence: 1,
        parts: [
          {
            type: "walkthrough",
            tour_id: "preview-canvas-two-step",
            title: "Guided canvas tour",
            description:
              "File and function nodes, then Monaco highlights on lines 3–5 and line 4 with popovers. Load the tour, open Canvas, press play.",
            icon: "map",
            workflow_name: "walkthrough:canvas-preview",
            walkthrough: AGENT_PREVIEW_CANVAS_WALKTHROUGH,
          },
        ],
        created_at: now,
        model: "preview",
      },
      {
        id: "preview-assistant-1",
        role: "assistant",
        sequence: 2,
        parts: [
          { type: "text", text: SAMPLE_MARKDOWN },
          {
            type: "task",
            task_id: "preview-task-1",
            title: "API middleware construction",
            description: "Secure routing and validation for public endpoints",
            state: "running",
            icon: "sparkles",
            workflow_name: "workflow:build",
            sub_task_count: 1,
            sub_tasks: [
              {
                title: "Scan environment",
                description: "Detect runtime, ports, and dependencies",
                state: "completed",
              },
            ],
          },
        ],
        created_at: now,
        model: "preview",
      },
      {
        id: "preview-assistant-2",
        role: "assistant",
        sequence: 3,
        parts: [
          {
            type: "task",
            task_id: "preview-task-1",
            title: "API middleware construction",
            description: "Secure routing and validation for public endpoints",
            state: "running",
            icon: "sparkles",
            workflow_name: "workflow:build",
            sub_task_count: 1,
            sub_tasks: [
              {
                title: "Scan environment",
                description: "Detect runtime, ports, and dependencies",
                state: "completed",
              },
              {
                title: "Generate secure logic",
                description: "Apply authn / authz templates",
                state: "pending",
              },
              {
                title: "Validate deployment",
                description: "Dry-run config against staging",
                state: "failed",
              },
            ],
          },
        ],
        created_at: now,
      },
    ],
  };
}
