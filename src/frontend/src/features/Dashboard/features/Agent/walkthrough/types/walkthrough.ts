/** Root walkthrough document */
export interface Walkthrough {
  meta: WalkthroughMeta;
  steps: WalkthroughStep[];
}

export interface WalkthroughMeta {
  id: string;
  title: string;
  description?: string;
  version: number;
}

export interface WalkthroughStep {
  id: string;
  actions: Action[];
  popover?: PopoverConfig;
}

export interface ActionBase {
  duration?: number;
}

export type Action =
  | FocusNodeAction
  | ExpandNodeAction
  | CollapseNodeAction
  | ShowCodeAction
  | CloseCodeAction
  | HighlightCodeAction
  | ClearHighlightAction
  | PanCanvasAction
  | SelectNodeAction
  | CreateTabAction
  | WaitAction;

export interface FocusNodeAction extends ActionBase {
  type: "focus-node";
  nodeId: string;
}

export interface ExpandNodeAction extends ActionBase {
  type: "expand-node";
  nodeId: string;
}

export interface CollapseNodeAction extends ActionBase {
  type: "collapse-node";
  nodeId: string;
}

export interface ShowCodeAction extends ActionBase {
  type: "show-code";
  nodeId: string;
}

export interface CloseCodeAction extends ActionBase {
  type: "close-code";
  nodeId: string;
}

export interface HighlightCodeAction extends ActionBase {
  type: "highlight-code";
  nodeId: string;
  lines: LineRange[];
  style?: HighlightStyle;
}

export interface ClearHighlightAction extends ActionBase {
  type: "clear-highlight";
  nodeId?: string;
}

export interface PanCanvasAction extends ActionBase {
  type: "pan-canvas";
  to: { nodeId: string };
}

export interface SelectNodeAction extends ActionBase {
  type: "select-node";
  nodeId: string;
  selectionType: "primary" | "secondary" | "promote";
}

export interface CreateTabAction extends ActionBase {
  type: "create-tab";
  nodeId: string;
}

export interface WaitAction extends ActionBase {
  type: "wait";
  ms: number;
}

export interface LineRange {
  from: number;
  to: number;
  label?: string;
}

export type HighlightStyle = "default" | "warning" | "added" | "removed" | "emphasis";

export interface PopoverConfig {
  title?: string;
  body: string;
  anchor: PopoverAnchor;
  side?: "top" | "bottom" | "left" | "right";
}

export type PopoverAnchor =
  | { type: "node"; nodeId: string }
  | { type: "code-line"; nodeId: string; line: number }
  | { type: "viewport-center" }
  | { type: "coordinates"; x: number; y: number };

/** Pre-computed timeline for the entire walkthrough */
export interface WalkthroughTimeline {
  totalDuration: number;
  steps: StepTimeline[];
}

export interface StepTimeline {
  stepIndex: number;
  stepId: string;
  startMs: number;
  endMs: number;
  actionsDuration: number;
  typewriterDuration: number;
  actions: ActionTimeline[];
}

export interface ActionTimeline {
  actionIndex: number;
  startMs: number;
  endMs: number;
  duration: number;
}

/** Resolved position within the walkthrough timeline */
export interface TimelinePosition {
  stepIndex: number;
  phase: "actions" | "typewriter" | "post-pause";
  actionIndex?: number;
  actionElapsedMs?: number;
  charIndex?: number;
}

export type EngineStatus = "idle" | "running" | "paused" | "complete";

export interface TypewriterState {
  fullText: string;
  visibleText: string;
  isTyping: boolean;
  charIndex: number;
}
