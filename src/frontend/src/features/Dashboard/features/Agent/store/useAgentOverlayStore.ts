import { create } from "zustand";

interface AgentOverlayState {
  isOpen: boolean;
  toggleOpen: () => void;
  setOpen: (open: boolean) => void;
}

export const useAgentOverlayStore = create<AgentOverlayState>((set) => ({
  isOpen: true,
  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (open) => set({ isOpen: open }),
}));
