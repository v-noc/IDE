import { create } from "zustand";

import { useWalkthroughStore } from "../walkthrough/store/useWalkthroughStore";

interface AgentOverlayState {
  isOpen: boolean;
  toggleOpen: () => void;
  setOpen: (open: boolean) => void;
}

export const useAgentOverlayStore = create<AgentOverlayState>((set, get) => ({
  isOpen: false,
  toggleOpen: () => {
    const next = !get().isOpen;
    if (next) {
      useWalkthroughStore.getState().setPlaybackDetached(false);
    }
    set({ isOpen: next });
  },
  setOpen: (open) => {
    if (open) {
      useWalkthroughStore.getState().setPlaybackDetached(false);
    }
    set({ isOpen: open });
  },
}));
