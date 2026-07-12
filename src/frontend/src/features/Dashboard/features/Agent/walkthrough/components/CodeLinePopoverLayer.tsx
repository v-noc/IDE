import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { StepPopover } from "./StepPopover";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { currentStepAnchor } from "../store/selectors";
import {
  WALKTHROUGH_POPOVER_GAP,
  WALKTHROUGH_POPOVER_H,
  WALKTHROUGH_POPOVER_W,
} from "./popoverLayout";

/**
 * Popover on the LEFT of the editor (keeps line numbers visible and pairs
 * with node-centered camera — right-side popover was clipped by the agent panel).
 */
function computePopoverPosition(editorRect: DOMRect) {
  let x = editorRect.left - WALKTHROUGH_POPOVER_W - WALKTHROUGH_POPOVER_GAP;
  let y =
    editorRect.top + editorRect.height / 2 - WALKTHROUGH_POPOVER_H / 2;

  if (x < 8) {
    x = editorRect.right + WALKTHROUGH_POPOVER_GAP;
  }

  y = Math.max(
    8,
    Math.min(y, window.innerHeight - WALKTHROUGH_POPOVER_H - 8),
  );

  return { x, y };
}

export function CodeLinePopoverLayer() {
  const phase = useWalkthroughStore((s) => s.phase);
  const stepDialogOpen = useWalkthroughStore((s) => s.stepDialogOpen);
  const anchorEpoch = useWalkthroughStore((s) => s.anchorEpoch);
  const anchorType = useWalkthroughStore((s) => {
    const anchor = currentStepAnchor(s);
    return anchor?.type ?? null;
  });
  const anchorNodeId = useWalkthroughStore((s) => {
    const anchor = currentStepAnchor(s);
    return anchor?.type === "code-line" ? anchor.nodeId : null;
  });
  const bumpAnchorEpoch = useWalkthroughStore((s) => s.bumpAnchorEpoch);

  useEffect(() => {
    const onResize = () => bumpAnchorEpoch();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [bumpAnchorEpoch]);

  const position = useMemo(() => {
    if (phase !== "playing" || anchorType !== "code-line" || !anchorNodeId) {
      return null;
    }

    const el = document.querySelector(
      `[data-walkthrough-editor-anchor][data-node-id="${anchorNodeId}"]`,
    );
    if (!el) return null;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return null;

    return computePopoverPosition(rect);
  }, [phase, anchorType, anchorNodeId, anchorEpoch]);

  if (
    phase !== "playing" ||
    anchorType !== "code-line" ||
    !position ||
    stepDialogOpen
  ) {
    return null;
  }

  return createPortal(
    <div
      className="pointer-events-auto fixed z-30"
      style={{
        left: position.x,
        top: position.y,
        width: WALKTHROUGH_POPOVER_W,
      }}
    >
      <StepPopover />
    </div>,
    document.body,
  );
}
