import { z } from "zod";
import type { Operation } from "fast-json-patch";

// ── Request & estimate ────────────────────────────────────────────────────────

export const runRequestSchema = z.object({
  project_id: z.string(),
  node_id: z.string(),
  depth: z.number().int().min(0).max(3),
});

export const estimateSchema = z.object({
  node_count: z.number().int().nonnegative(),
  step_estimate: z.number().int().nonnegative(),
  llm_call_estimate: z.number().int().nonnegative(),
  over_cap: z.boolean(),
});

// ── Visit list ────────────────────────────────────────────────────────────────

export const nodeTypeSchema = z.enum([
  "folder",
  "file",
  "class",
  "function",
  "call",
]);

export const visitModeSchema = z.enum(["full", "contextual"]);

export const visitNodeSchema = z.object({
  node_id: z.string(),
  name: z.string(),
  qname: z.string().nullable(),
  node_type: nodeTypeSchema,
  description: z.string(),
  level: z.number().int().nonnegative(),
  order: z.number().int().nonnegative(),
  parent_order: z.number().int().nullable(),
  target_id: z.string().nullable(),
  mode: visitModeSchema,
  first_seen_order: z.number().int().nullable(),
  has_code: z.boolean(),
  start_line: z.number().int().nullable(),
  end_line: z.number().int().nullable(),
  line_count: z.number().int().nullable(),
  gated: z.boolean(),
});

export const visitListSchema = z.object({
  start_node_id: z.string(),
  depth: z.number().int(),
  nodes: z.array(visitNodeSchema),
});

// ── Steps ─────────────────────────────────────────────────────────────────────

export const blockStepSchema = z.object({
  index: z.number().int().nonnegative(),
  start_line: z.number().int(),
  end_line: z.number().int(),
  focus: z.string(),
  text: z.string(),
  degraded: z.boolean(),
});

export const nodeStepsSchema = z.object({
  node_id: z.string(),
  order: z.number().int().nonnegative(),
  mode: visitModeSchema,
  intro_text: z.string(),
  degraded: z.boolean(),
  blocks: z.array(blockStepSchema),
});

export const tokenUsageSchema = z.object({
  prompt_tokens: z.number().int().nonnegative(),
  completion_tokens: z.number().int().nonnegative(),
});

export const sessionStatusSchema = z.enum([
  "generating",
  "complete",
  "error",
  "aborted",
]);

export const walkthroughSessionSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  request: runRequestSchema,
  branch: z.string(),
  commit_id: z.string(),
  visit_list: visitListSchema,
  node_steps: z.array(nodeStepsSchema),
  status: sessionStatusSchema,
  error_log: z.array(z.string()),
  schema_version: z.string(),
  prompt_version: z.string(),
  model_id: z.string(),
  usage: tokenUsageSchema,
});

// ── Player ────────────────────────────────────────────────────────────────────

export const actionSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("select_node"), nodeId: z.string() }),
  z.object({ type: z.literal("show_code"), nodeId: z.string() }),
  z.object({
    type: z.literal("highlight_lines"),
    nodeId: z.string(),
    startLine: z.number().int(),
    endLine: z.number().int(),
  }),
]);

// ── Wire frames ───────────────────────────────────────────────────────────────

export const helloFrameSchema = z.object({
  kind: z.literal("hello"),
  protocol: z.literal(1),
  session: walkthroughSessionSchema,
});

export const patchFrameSchema = z.object({
  kind: z.literal("patch"),
  seq: z.number().int().nonnegative(),
  ops: z.array(z.custom<Operation>()),
});

export const endFrameSchema = z.object({
  kind: z.literal("end"),
  status: z.enum(["complete", "error"]),
  message: z.string().optional(),
});

export const frameSchema = z.discriminatedUnion("kind", [
  helloFrameSchema,
  patchFrameSchema,
  endFrameSchema,
]);

export const mockFixtureSchema = z.object({
  estimate: estimateSchema,
  frames: z.array(
    z.object({
      delay: z.number().int().nonnegative(),
      frame: frameSchema,
    }),
  ),
});

// ── Inferred types ────────────────────────────────────────────────────────────

export type RunRequest = z.infer<typeof runRequestSchema>;
export type Estimate = z.infer<typeof estimateSchema>;
export type VisitNode = z.infer<typeof visitNodeSchema>;
export type VisitList = z.infer<typeof visitListSchema>;
export type BlockStep = z.infer<typeof blockStepSchema>;
export type NodeSteps = z.infer<typeof nodeStepsSchema>;
export type WalkthroughSession = z.infer<typeof walkthroughSessionSchema>;
export type Action = z.infer<typeof actionSchema>;
export type Frame = z.infer<typeof frameSchema>;
export type MockFixture = z.infer<typeof mockFixtureSchema>;

export type WalkthroughPhase =
  | "idle"
  | "generating"
  | "ready"
  | "playing"
  | "error";

export interface PlayerStep {
  id: string;
  nodeId: string;
  actions: Action[];
  title: string;
  text: string;
  degraded: boolean;
  visitOrder: number;
}

export interface SavedView {
  tabId: string;
  selectedNodeId: string | null;
  secondarySelectedNodeId: string | null;
  expandedNodeIds: string[];
  focusStack: string[];
}

export function parseFrame(raw: unknown): Frame | null {
  const result = frameSchema.safeParse(raw);
  if (!result.success) {
    console.warn("[walkthrough] invalid frame", result.error.flatten());
    return null;
  }
  return result.data;
}
