import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { Operation } from "fast-json-patch";
import type {
  PlayerStep,
  RunRequest,
  SavedView,
  WalkthroughPhase,
  WalkthroughSession,
} from "../types";
import { applyFrame, applyOpsToSession } from "../source/applyFrame";
import { walkthroughSource } from "../source";
import {
  findStepIndex,
  flattenSession,
  firstStepIdForVisit,
} from "./flatten";
import { captureSavedView, restoreSavedView } from "../executor/restoreView";
import { prepareTour } from "../executor/prepareTour";
import { queryClient } from "@/lib/queryClient";

interface WalkthroughState {
  phase: WalkthroughPhase;
  error: string | null;
  session: WalkthroughSession | null;
  lastSeq: number;
  playerSteps: PlayerStep[];
  tabId: string | null;
  cursor: number;
  userInteracted: boolean;
  savedView: SavedView | null;
  highlight: {
    nodeId: string;
    startLine: number;
    endLine: number;
  } | null;
  codeOpenNodeId: string | null;
  pendingAdvance: boolean;
  preparing: boolean;
  tourPrepared: boolean;

  start: (req: RunRequest, tabId: string) => void;
  applyOps: (ops: Operation[]) => void;
  handleFrameResult: (result: ReturnType<typeof applyFrame>) => void;
  play: () => void;
  exit: () => void;
  next: () => void;
  prev: () => void;
  jumpTo: (stepId: string) => void;
  discard: () => void;
  setUserInteracted: (value: boolean) => void;
  setSavedView: (view: SavedView | null) => void;
  setHighlight: (
    highlight: WalkthroughState["highlight"],
  ) => void;
  setCodeOpenNodeId: (nodeId: string | null) => void;
  clearHighlight: () => void;
}

let abortController: AbortController | null = null;

function syncDerived(state: WalkthroughState) {
  state.playerSteps = state.session ? flattenSession(state.session) : [];
}

function clampCursor(cursor: number, stepCount: number): number {
  if (stepCount === 0) return -1;
  return Math.max(0, Math.min(cursor, stepCount - 1));
}

const initialState = {
  phase: "idle" as WalkthroughPhase,
  error: null,
  session: null,
  lastSeq: -1,
  playerSteps: [] as PlayerStep[],
  tabId: null,
  cursor: -1,
  userInteracted: false,
  savedView: null,
  highlight: null,
  codeOpenNodeId: null,
  pendingAdvance: false,
  preparing: false,
  tourPrepared: false,
};

export const useWalkthroughStore = create<WalkthroughState>()(
  devtools(
    immer((set, get) => ({
      ...initialState,

      start(req, tabId) {
        abortController?.abort();
        abortController = new AbortController();
        const signal = abortController.signal;

        set((state) => {
          Object.assign(state, initialState);
          state.phase = "generating";
          state.tabId = tabId;
        });

        void (async () => {
          try {
            await walkthroughSource.run(
              req,
              (frame) => {
                const current = get();
                const result = applyFrame(frame, {
                  session: current.session,
                  lastSeq: current.lastSeq,
                  phase: current.phase,
                });
                get().handleFrameResult(result);
              },
              signal,
            );
          } catch (err) {
            if (signal.aborted) return;
            set((state) => {
              state.phase = "error";
              state.error =
                err instanceof Error ? err.message : "Generation failed";
            });
          }
        })();
      },

      applyOps(ops) {
        set((state) => {
          if (!state.session) return;
          state.session = applyOpsToSession(state.session, ops);
          syncDerived(state);
        });
      },

      handleFrameResult(result) {
        set((state) => {
          state.session = result.session;
          state.lastSeq = result.lastSeq;
          state.phase = result.phase;
          state.error = result.error;
          syncDerived(state);

          if (
            state.pendingAdvance &&
            state.phase === "playing" &&
            state.cursor < state.playerSteps.length - 1
          ) {
            state.cursor += 1;
            state.pendingAdvance = false;
          }

          if (
            state.phase === "playing" &&
            state.cursor >= 0 &&
            state.cursor >= state.playerSteps.length
          ) {
            state.cursor = Math.max(0, state.playerSteps.length - 1);
          }
        });
      },

      play() {
        const current = get();
        if (
          !current.session ||
          current.playerSteps.length === 0 ||
          current.preparing
        ) {
          return;
        }

        set((state) => {
          if (!state.savedView && state.tabId) {
            state.savedView = captureSavedView(state.tabId);
          }
          state.preparing = true;
          state.userInteracted = false;
        });

        void (async () => {
          const { tabId, session } = get();
          if (!tabId || !session) {
            set((state) => {
              state.preparing = false;
            });
            return;
          }

          // On Play: materialize and expand every tour stop up front, so the canvas
          // layout is final before the first step. Step 0 focuses the tour root at
          // zoom 1; later steps slide at the current zoom when needed. The tour
          // drives the camera alone while playing.
          await prepareTour(queryClient, tabId, session);

          set((state) => {
            state.preparing = false;
            state.tourPrepared = true;
            state.phase = "playing";
            state.cursor = state.cursor < 0 ? 0 : state.cursor;
          });
        })();
      },

      exit() {
        const savedView = get().savedView;
        set((state) => {
          state.phase = state.session ? "ready" : "idle";
          state.userInteracted = false;
          state.highlight = null;
          state.codeOpenNodeId = null;
          state.pendingAdvance = false;
        });
        if (savedView) {
          restoreSavedView(savedView);
        }
      },

      next() {
        set((state) => {
          if (state.playerSteps.length === 0 || state.phase !== "playing") return;

          const nextCursor = state.cursor + 1;
          if (nextCursor < state.playerSteps.length) {
            state.cursor = nextCursor;
            state.userInteracted = false;
            state.pendingAdvance = false;
            return;
          }

          if (state.session?.status === "generating") {
            state.pendingAdvance = true;
          }
        });
      },

      prev() {
        set((state) => {
          if (state.cursor > 0) {
            state.cursor -= 1;
            state.userInteracted = false;
            state.pendingAdvance = false;
          }
        });
      },

      jumpTo(stepId) {
        const index = findStepIndex(get().playerSteps, stepId);
        if (index < 0) return;

        if (get().preparing) return;

        set((state) => {
          if (!state.savedView && state.tabId) {
            state.savedView = captureSavedView(state.tabId);
          }
          state.preparing = true;
        });

        void (async () => {
          const { tabId, session, tourPrepared } = get();
          if (!tabId || !session) {
            set((state) => {
              state.preparing = false;
            });
            return;
          }

          if (!tourPrepared) {
            await prepareTour(queryClient, tabId, session);
          }

          set((state) => {
            state.preparing = false;
            state.tourPrepared = true;
            state.phase = "playing";
            state.cursor = index;
            state.userInteracted = false;
            state.pendingAdvance = false;
          });
        })();
      },

      discard() {
        abortController?.abort();
        abortController = null;
        const savedView = get().savedView;
        if (savedView) {
          restoreSavedView(savedView);
        }
        set((state) => {
          Object.assign(state, initialState);
        });
      },

      setUserInteracted(value) {
        set((state) => {
          state.userInteracted = value;
        });
      },

      setSavedView(view) {
        set((state) => {
          state.savedView = view;
        });
      },

      setHighlight(highlight) {
        set((state) => {
          state.highlight = highlight;
        });
      },

      setCodeOpenNodeId(nodeId) {
        set((state) => {
          state.codeOpenNodeId = nodeId;
        });
      },

      clearHighlight() {
        set((state) => {
          state.highlight = null;
        });
      },
    })),
    { name: "walkthrough-store" },
  ),
);

export function jumpToVisit(order: number) {
  useWalkthroughStore.getState().jumpTo(firstStepIdForVisit(order));
}

export function selectPlayerSteps() {
  return useWalkthroughStore.getState().playerSteps;
}

export function selectCurrentStep(): PlayerStep | null {
  const { playerSteps, cursor } = useWalkthroughStore.getState();
  if (cursor < 0 || cursor >= playerSteps.length) return null;
  return playerSteps[cursor];
}

export function isCurrentStepNode(nodeId: string): boolean {
  const { phase, cursor, playerSteps } = useWalkthroughStore.getState();
  return phase === "playing" && playerSteps[cursor]?.nodeId === nodeId;
}

export { clampCursor };
