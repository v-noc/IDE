import { useEffect } from "react";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

const DIM_CLASS = "walkthrough-dimmed";
const HIGHLIGHT_CLASS = "walkthrough-highlighted";
const FLOW_FOCUS_CLASS = "walkthrough-focus-active";
const MAX_FRAMES = 180;

export function SpotlightOverlay() {
  const spotlightNodeId = useWalkthroughStore((s) => s.spotlightNodeId);

  useEffect(() => {
    const allNodesStatic = () =>
      Array.from(document.querySelectorAll<HTMLElement>(".react-flow__node"));

    if (!spotlightNodeId) {
      for (const node of allNodesStatic()) {
        node.classList.remove(DIM_CLASS, HIGHLIGHT_CLASS);
      }
      document
        .querySelector<HTMLElement>(".react-flow")
        ?.classList.remove(FLOW_FOCUS_CLASS);
      return;
    }

    let cancelled = false;
    let frame = 0;
    let rafId = 0;
    const clearAll = () => {
      for (const node of allNodesStatic()) {
        node.classList.remove(DIM_CLASS, HIGHLIGHT_CLASS);
      }
      document
        .querySelector<HTMLElement>(".react-flow")
        ?.classList.remove(FLOW_FOCUS_CLASS);
    };

    const apply = (target: HTMLElement) => {
      const flowRootLocal =
        target.closest<HTMLElement>(".react-flow") ??
        document.querySelector<HTMLElement>(".react-flow");

      const allNodes = allNodesStatic();
      for (const node of allNodes) {
        if (node === target) {
          node.classList.add(HIGHLIGHT_CLASS);
          node.classList.remove(DIM_CLASS);
        } else {
          node.classList.add(DIM_CLASS);
          node.classList.remove(HIGHLIGHT_CLASS);
        }
      }
      flowRootLocal?.classList.add(FLOW_FOCUS_CLASS);
      target.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
    };

    const tick = () => {
      if (cancelled) return;
      const target = document.querySelector<HTMLElement>(
        `.react-flow__node[data-id="${cssEscape(spotlightNodeId)}"]`,
      );
      if (target) {
        apply(target);
        return;
      }
      frame += 1;
      if (frame < MAX_FRAMES) {
        rafId = requestAnimationFrame(tick);
      }
    };

    tick();

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      clearAll();
    };
  }, [spotlightNodeId]);

  return null;
}

function cssEscape(value: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(value);
  }
  return value.replace(/["\\]/g, "\\$&");
}
