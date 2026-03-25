import type { WireConversation } from "@/types/agent";

/** Local-only conversation id: skips REST hydration and socket room join. */
export const AGENT_UI_PREVIEW_CONVERSATION_ID = "__vnoc_agent_ui_preview__";

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
    description: "Local fixture for markdown + task layout",
    message_count: 3,
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
            text: "Show markdown formatting and a task with sub-tasks.",
          },
        ],
        created_at: now,
      },
      {
        id: "preview-assistant-1",
        role: "assistant",
        sequence: 1,
        parts: [{ type: "text", text: SAMPLE_MARKDOWN }, {
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
            },]
        }],
        created_at: now,
        model: "preview",
      },
      {
        id: "preview-assistant-2",
        role: "assistant",
        sequence: 2,
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
