import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { StepPopover } from "./StepPopover";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { currentStepAnchor } from "../store/selectors";

const POPOVER_W = 360;
const POPOVER_ESTIMATE_H = 200;

function computePopoverPosition(rect: DOMRect) {
  let x = rect.left - POPOVER_W - 12;
  let y = rect.top + rect.height / 2 - POPOVER_ESTIMATE_H / 2;

  if (x < 8) {
    x = rect.right + 12;
  }

  y = Math.max(8, Math.min(y, window.innerHeight - POPOVER_ESTIMATE_H - 8));

  if (rect.right < 0) {
    x = 8;
  } else if (rect.left > window.innerWidth) {
    x = window.innerWidth - POPOVER_W - 8;
  }

  return { x, y };
}

export function CodeLinePopoverLayer() {
  const phase = useWalkthroughStore((s) => s.phase);
  const anchorEpoch = useWalkthroughStore((s) => s.anchorEpoch);
  const anchorType = useWalkthroughStore((s) => {
    const anchor = currentStepAnchor(s);
    return anchor?.type ?? null;
  });
  const anchorNodeId = useWalkthroughStore((s) => {
    const anchor = currentStepAnchor(s);
    return anchor?.type === "code-line" ? anchor.nodeId : null;
  });
  const anchorLine = useWalkthroughStore((s) => {
    const anchor = currentStepAnchor(s);
    return anchor?.type === "code-line" ? anchor.line : null;
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
      `[data-walkthrough-code-anchor][data-node-id="${anchorNodeId}"]`,
    );
    if (!el) return null;

    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return null;

    return computePopoverPosition(rect);
    // anchorLine included so step changes re-measure even at same epoch
  }, [phase, anchorType, anchorNodeId, anchorLine, anchorEpoch]);

  if (phase !== "playing" || anchorType !== "code-line" || !position) {
    return null;
  }

  return createPortal(
    <div
      className="pointer-events-auto fixed z-30"
      style={{
        left: position.x,
        top: position.y,
        width: POPOVER_W,
      }}
    >
      <StepPopover />
    </div>,
    document.body,
  );
}
