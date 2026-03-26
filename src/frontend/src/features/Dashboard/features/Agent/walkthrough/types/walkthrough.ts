interface Walkthrough {
  meta: WalkthroughMeta;
  steps: WalkthroughStep[];
}

interface WalkthroughMeta {
  id: string;
  title: string;
  description?: string;
  version: number;
}

interface WalkthroughStep {
  id: string;
  actions: Action[];
  popover?: PopoverConfig;
}

interface ActionBase {
  duration?: number;


}

type Action =
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

// ─── Individual Action Types ───────────────────────────

interface FocusNodeAction extends ActionBase {
  type: "focus-node";
  nodeId: string;
}

interface ExpandNodeAction extends ActionBase {
  type: "expand-node";
  nodeId: string;
}

interface CollapseNodeAction extends ActionBase {
  type: "collapse-node";
  nodeId: string;
}

/** Toggle the code view ON for a node (distinct from expand which shows children) */
interface ShowCodeAction extends ActionBase {
  type: "show-code";
  nodeId: string;
}

/** Toggle the code view OFF for a node */
interface CloseCodeAction extends ActionBase {
  type: "close-code";
  nodeId: string;
}

interface HighlightCodeAction extends ActionBase {
  type: "highlight-code";
  nodeId: string;
  lines: LineRange[];
  style?: HighlightStyle;
}

interface ClearHighlightAction extends ActionBase {
  type: "clear-highlight";
  nodeId?: string;           // if omitted, clear ALL highlights
}

interface PanCanvasAction extends ActionBase {
  type: "pan-canvas";
  to: { nodeId: string };    // pan + center on this node
}

interface SelectNodeAction extends ActionBase {
  type: "select-node";
  nodeId: string;
  selectionType: "primary" | "secondary" | "promote";
}

interface CreateTabAction extends ActionBase {
  type: "create-tab";
  nodeId: string;            // the call node whose target becomes the tab
}

interface WaitAction extends ActionBase {
  type: "wait";
  ms: number;                // explicit wait duration (overrides ActionBase.duration)
}

interface LineRange {
  from: number;              // 1-based line number
  to: number;                // 1-based, inclusive
  label?: string;            // optional inline annotation text
}

type HighlightStyle = "default" | "warning" | "added" | "removed" | "emphasis";

interface PopoverConfig {
  title?: string;
  body: string;                        // markdown or plain text — displayed with typewriter effect
  anchor: PopoverAnchor;
  side?: "top" | "bottom" | "left" | "right";   // preferred placement
}

type PopoverAnchor =
  | { type: "node"; nodeId: string }
  | { type: "code-line"; nodeId: string; line: number }
  | { type: "viewport-center" }
  | { type: "coordinates"; x: number; y: number };

/** Pre-computed timeline for the entire walkthrough */
interface WalkthroughTimeline {
  totalDuration: number;              // total walkthrough duration in ms
  steps: StepTimeline[];
}

interface StepTimeline {
  stepIndex: number;
  stepId: string;
  startMs: number;                    // absolute start time of this step
  endMs: number;                      // absolute end time of this step
  actionsDuration: number;            // total duration of all actions
  typewriterDuration: number;         // duration of typewriter animation
  actions: ActionTimeline[];          // per-action timing
}

interface ActionTimeline {
  actionIndex: number;
  startMs: number;                    // relative to step start
  endMs: number;                      // relative to step start
  duration: number;                   // this action's duration
}

/** Resolved position within the walkthrough timeline */
interface TimelinePosition {
  stepIndex: number;
  phase: "actions" | "typewriter" | "post-pause";
  actionIndex?: number;               // if phase is "actions"
  actionElapsedMs?: number;           // how far into the current action
  charIndex?: number;                 // if phase is "typewriter" — which character to show up to
}


/** Context passed to every handler — provides access to adapters + stores */
interface ActionContext {
  adapter: CanvasAdapter;
  signal: AbortSignal;
  cleanup: CleanupStack;
}

/** Return type: handlers can optionally return a teardown function */
type ActionHandler<T extends Action = Action> = (
  action: T,
  ctx: ActionContext,
) => Promise<void>;

type EngineStatus = "idle" | "running" | "paused" | "complete";

interface TypewriterState {
  fullText: string;          // the complete text to display
  visibleText: string;       // currently revealed portion
  isTyping: boolean;         // animation in progress
  charIndex: number;         // current position
}
