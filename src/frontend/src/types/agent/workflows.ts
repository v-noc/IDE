/** Matches backend `OpenAIProvider.supported_models` defaults. */
export const WORKFLOW_MODEL_OPTIONS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-3.5-turbo",
] as const;

export type WorkflowModelId = (typeof WORKFLOW_MODEL_OPTIONS)[number];

export type AgentWorkflowName =
  | "description_generator"
  | "documentation_generator";

export type DescriptionWorkflowMode = "always" | "skip_if_present";

export type DocumentationWorkflowMode = "upsert" | "insert_only";

export interface WorkflowBatchStepWire {
  workflow_name: AgentWorkflowName;
  params: Record<string, unknown>;
}

/** Dialog payload: each step is started with `POST .../workflows/run` in order, reusing `conversation_id`. */
export interface StartAgentWorkflowsPayload {
  steps: WorkflowBatchStepWire[];
  conversation_title?: string | null;
  conversation_description?: string | null;
}

export interface RunWorkflowRequest {
  workflow_name: AgentWorkflowName;
  params: Record<string, unknown>;
  conversation_id?: string | null;
  message_id?: string | null;
  conversation_title?: string | null;
  conversation_description?: string | null;
}

export interface RunWorkflowResponse {
  conversation_id: string;
  task_id: string;
  status: string;
}
