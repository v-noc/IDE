import type { AnyNodeTree } from '@/types/project';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

type ModalType =
  | 'create-group'
  | 'manage-group'
  | 'add-call'
  | 'prompt-builder'
  | 'edit-virtual-folder'
  | 'select-node'
  | 'demo-read-only'
  | null;

interface SidebarModalState {
  // State
  activeModal: ModalType;
  targetNode: AnyNodeTree | null;

  // Actions
  openModal: (type: ModalType, node: AnyNodeTree) => void;
  /** Opens the demo read-only dialog without requiring a sidebar target node (e.g. API guard). */
  openReadOnlyModal: () => void;
  closeModal: () => void;
}

export const useSidebarModalStore = create<SidebarModalState>()(
  devtools(
    (set) => ({
      activeModal: null,
      targetNode: null,

      openModal: (type, node) => set({
        activeModal: type,
        targetNode: node
      }),

      openReadOnlyModal: () => set({ activeModal: 'demo-read-only' }),

      closeModal: () => set({
        activeModal: null,
        targetNode: null
      }),
    }),
    { name: 'sidebar-modals' }
  )
);

// Selectors for performance
export const useActiveModal = () => useSidebarModalStore((s) => s.activeModal);
export const useTargetNode = () => useSidebarModalStore((s) => s.targetNode);
export const useOpenModal = () => useSidebarModalStore((s) => s.openModal);
export const useCloseModal = () => useSidebarModalStore((s) => s.closeModal);
