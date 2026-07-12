import { useEffect, useEffectEvent } from "react";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

/**
 * Arrow-key navigation while a tour is playing.
 * Uses useEffectEvent so the handler always reads fresh store actions
 * without re-subscribing the key listener on every render.
 */
export function useWalkthroughKeyboard() {
  const phase = useWalkthroughStore((s) => s.phase);

  const onKeyDown = useEffectEvent((event: KeyboardEvent) => {
    if (phase !== "playing") return;

    const target = event.target as HTMLElement | null;
    const tag = target?.tagName.toLowerCase();
    if (
      tag === "input" ||
      tag === "textarea" ||
      target?.isContentEditable
    ) {
      return;
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      useWalkthroughStore.getState().next();
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      useWalkthroughStore.getState().prev();
    }

    if (event.key === "Escape") {
      if (useWalkthroughStore.getState().stepDialogOpen) {
        return;
      }
      event.preventDefault();
      useWalkthroughStore.getState().exit();
    }
  });

  useEffect(() => {
    if (phase !== "playing") return;

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [phase, onKeyDown]);
}
