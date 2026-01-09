import { useState, useRef, useCallback } from 'react';
import type { ImperativePanelHandle } from 'react-resizable-panels';

export function usePanelState(defaultOpen = true) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const ref = useRef<ImperativePanelHandle>(null);



  const toggle = useCallback(() => {
    const panel = ref.current;
    if (!panel) return;

    if (isOpen) {
      panel.collapse();
    } else {
      panel.expand();
    }
    setIsOpen(!isOpen);
  }, [isOpen])

  const open = useCallback(() => {
    const panel = ref.current;
    if (panel && !isOpen) {
      panel.expand();
      setIsOpen(true);
    }
  }, [isOpen])

  const close = useCallback(() => {
    const panel = ref.current;
    if (panel && isOpen) {
      panel.collapse();
      setIsOpen(false);
    }
  }, [isOpen])

  return {
    isOpen,
    toggle,
    open,
    close,
    ref,
    onCollapse: () => setIsOpen(false),
    onExpand: () => setIsOpen(true)
  };
}
