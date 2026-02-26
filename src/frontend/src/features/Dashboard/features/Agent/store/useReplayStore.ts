import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { ReplayEvent } from "../types/conversation";
import type { RunnerStatus } from "../engine/ReplayRunner";

interface ReplayState {
  status: RunnerStatus;
  currentIndex: number;
  currentEvent: ReplayEvent | null;
  totalEvents: number;
  speed: number;
  setStatus: (status: RunnerStatus) => void;
  setProgress: (index: number, event: ReplayEvent | null) => void;
  setTotalEvents: (total: number) => void;
  setSpeed: (speed: number) => void;
  reset: () => void;
}

export const useReplayStore = create<ReplayState>()(
  devtools(
    (set) => ({
      status: "idle",
      currentIndex: 0,
      currentEvent: null,
      totalEvents: 0,
      speed: 1,
      setStatus: (status) => set({ status }),
      setProgress: (index, event) =>
        set({ currentIndex: Math.max(0, index), currentEvent: event }),
      setTotalEvents: (total) => set({ totalEvents: Math.max(0, total) }),
      setSpeed: (speed) => set({ speed }),
      reset: () =>
        set({
          status: "idle",
          currentIndex: 0,
          currentEvent: null,
        }),
    }),
    { name: "replay-store" },
  ),
);
