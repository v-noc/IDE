import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { StepPopover } from "./StepPopover";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { currentStepAnchor } from "../store/selectors";
import {
  WALKTHROUGH_POPOVER_GAP,
  WALKTHROUGH_POPOVER_W,
} from "./popoverLayout";

/**
 * Popover on the LEFT of the node (keeps line numbers visible and pairs
 * with node-centered camera — right-side popover was clipped by the agent panel).
 */
function computePopoverPosition(nodeRect: DOMRect) {
  let x = nodeRect.left - WALKTHROUGH_POPOVER_W - WALKTHROUGH_POPOVER_GAP;
  const centerY = nodeRect.top + nodeRect.height / 2;

  if (x < 8) {
    x = nodeRect.right + WALKTHROUGH_POPOVER_GAP;
  }

  return { x, centerY };
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

    const el =
      document.querySelector(
        `[data-walkthrough-node-anchor][data-node-id="${anchorNodeId}"]`,
      ) ??
      document.querySelector(
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
        top: position.centerY,
        transform: "translateY(-50%)",
        width: WALKTHROUGH_POPOVER_W,
      }}
    >
      <StepPopover />
    </div>,
    document.body,
  );
}
