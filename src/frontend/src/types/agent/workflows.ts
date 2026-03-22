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

export interface RunWorkflowBatchRequest {
  steps: WorkflowBatchStepWire[];
  conversation_id?: string | null;
  conversation_title?: string | null;
  conversation_description?: string | null;
}

export interface RunWorkflowBatchResponse {
  conversation_id: string;
  task_ids: string[];
  status: string;
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
