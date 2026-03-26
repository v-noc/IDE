import { create } from "zustand";
import { devtools } from "zustand/middleware";

import type {
  EngineStatus,
  HighlightStyle,
  LineRange,
  PopoverConfig,
  TypewriterState,
  Walkthrough,
  WalkthroughTimeline,
} from "../types/walkthrough";

export interface WalkthroughControls {
  load: (walkthrough: Walkthrough) => void;
  play: () => Promise<void>;
  pause: () => void;
  stop: () => void;
  next: () => Promise<void>;
  prev: () => Promise<void>;
  seekToStep: (stepId: string) => Promise<void>;
  seekToTime: (ms: number) => Promise<void>;
  setSpeed: (speed: number) => void;
}

const initialTypewriter: TypewriterState = {
  fullText: "",
  visibleText: "",
  isTyping: false,
  charIndex: 0,
};

export interface WalkthroughStoreState {
  status: EngineStatus;
  walkthrough: Walkthrough | null;
  timeline: WalkthroughTimeline | null;
  elapsedMs: number;
  currentStepIndex: number;
  currentStepId: string | null;
  totalSteps: number;
  speed: number;

  popover: PopoverConfig | null;
  popoverVisible: boolean;

  typewriter: TypewriterState;

  spotlightNodeId: string | null;
  highlights: Map<string, { lines: LineRange[]; style?: HighlightStyle }>;

  /** Node ids whose inline code panel is forced open by the walkthrough adapter. */
  forcedCodeOpen: Record<string, boolean>;

  /**
   * Bumped when an inline Monaco line anchor moves (scroll/layout) so PopoverLayer
   * can re-read viewport coordinates for `code-line` anchors.
   */
  codeAnchorLayoutEpoch: number;

  controls: WalkthroughControls | null;

  /** When true, agent sidebar is hidden and the playback bar is shown on the canvas. */
  playbackDetached: boolean;
  setPlaybackDetached: (detached: boolean) => void;

  setStatus: (status: EngineStatus) => void;
  setWalkthrough: (wt: Walkthrough | null) => void;
  setTimeline: (timeline: WalkthroughTimeline | null) => void;
  setElapsedMs: (ms: number) => void;
  setCurrentStep: (index: number, stepId: string | null) => void;
  setSpeed: (speed: number) => void;

  setPopover: (config: PopoverConfig | null) => void;
  setPopoverVisible: (visible: boolean) => void;

  setTypewriter: (partial: Partial<TypewriterState>) => void;
  resetTypewriter: (fullText: string) => void;

  setSpotlightNodeId: (nodeId: string | null) => void;

  setHighlight: (
    nodeId: string,
    lines: LineRange[],
    style?: HighlightStyle,
  ) => void;
  clearHighlightStore: (nodeId?: string) => void;

  setForcedCodeOpen: (nodeId: string, open: boolean) => void;
  clearForcedCodeOpen: () => void;

  bumpCodeAnchorLayoutEpoch: () => void;

  setControls: (controls: WalkthroughControls | null) => void;

  reset: () => void;
}

export const useWalkthroughStore = create<WalkthroughStoreState>()(
  devtools(
    (set) => ({
      status: "idle",
      walkthrough: null,
      timeline: null,
      elapsedMs: 0,
      currentStepIndex: 0,
      currentStepId: null,
      totalSteps: 0,
      speed: 1,

      popover: null,
      popoverVisible: false,

      typewriter: { ...initialTypewriter },

      spotlightNodeId: null,
      highlights: new Map(),

      forcedCodeOpen: {},

      codeAnchorLayoutEpoch: 0,

      controls: null,

      playbackDetached: false,
      setPlaybackDetached: (detached) => set({ playbackDetached: detached }),

      setStatus: (status) => set({ status }),

      setWalkthrough: (wt) =>
        set({
          walkthrough: wt,
          totalSteps: wt?.steps.length ?? 0,
          currentStepIndex: 0,
          currentStepId: wt?.steps[0]?.id ?? null,
          forcedCodeOpen: {},
        }),

      setTimeline: (timeline) => set({ timeline }),

      setElapsedMs: (ms) => set({ elapsedMs: Math.max(0, ms) }),

      setCurrentStep: (index, stepId) =>
        set({ currentStepIndex: index, currentStepId: stepId }),

      setSpeed: (speed) => set({ speed }),

      setPopover: (config) =>
        set({
          popover: config,
          popoverVisible: config != null,
        }),

      setPopoverVisible: (visible) => set({ popoverVisible: visible }),

      setTypewriter: (partial) =>
        set((state) => ({
          typewriter: { ...state.typewriter, ...partial },
        })),

      resetTypewriter: (fullText) =>
        set({
          typewriter: {
            fullText,
            visibleText: "",
            isTyping: true,
            charIndex: 0,
          },
        }),

      setSpotlightNodeId: (nodeId) => set({ spotlightNodeId: nodeId }),

      setHighlight: (nodeId, lines, style) =>
        set((state) => {
          const next = new Map(state.highlights);
          next.set(nodeId, { lines, style });
          return { highlights: next };
        }),

      clearHighlightStore: (nodeId) =>
        set((state) => {
          if (!nodeId) return { highlights: new Map() };
          const next = new Map(state.highlights);
          next.delete(nodeId);
          return { highlights: next };
        }),

      setForcedCodeOpen: (nodeId, open) =>
        set((state) => {
          const next = { ...state.forcedCodeOpen };
          if (open) {
            next[nodeId] = true;
          } else {
            delete next[nodeId];
          }
          return { forcedCodeOpen: next };
        }),

      clearForcedCodeOpen: () => set({ forcedCodeOpen: {} }),

      bumpCodeAnchorLayoutEpoch: () =>
        set((s) => ({ codeAnchorLayoutEpoch: s.codeAnchorLayoutEpoch + 1 })),

      setControls: (controls) => set({ controls }),

      reset: () =>
        set({
          status: "idle",
          walkthrough: null,
          timeline: null,
          elapsedMs: 0,
          currentStepIndex: 0,
          currentStepId: null,
          totalSteps: 0,
          speed: 1,
          popover: null,
          popoverVisible: false,
          typewriter: { ...initialTypewriter },
          spotlightNodeId: null,
          highlights: new Map(),
          forcedCodeOpen: {},
          codeAnchorLayoutEpoch: 0,
          controls: null,
          playbackDetached: false,
        }),
    }),
    { name: "walkthrough-store" },
  ),
);

export type WalkthroughStoreApi = typeof useWalkthroughStore;
