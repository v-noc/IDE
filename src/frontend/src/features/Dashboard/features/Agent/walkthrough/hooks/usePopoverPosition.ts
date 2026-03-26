import { useMemo } from "react";
import { useReactFlow } from "@xyflow/react";
import type { PopoverAnchor } from "../types/walkthrough";

/** Space between anchor (node edge) and popover content; keep in sync with PopoverContent `sideOffset`. */
export const WALKTHROUGH_POPOVER_GAP = 12;

function safeCssId(id: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(id);
  }
  return id.replace(/["\\]/g, "\\$&");
}

/** Midpoint on the node/canvas rect edge — Radix positions content on `side` with `sideOffset` beyond this point. */
/** Anchor point on a small rect (e.g. one editor line) for Radix `side`. */
function edgePointFromAnchorRect(
  rect: DOMRect,
  side: "top" | "bottom" | "left" | "right",
): { x: number; y: number } {
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  switch (side) {
    case "top":
      return { x: cx, y: rect.top };
    case "bottom":
      return { x: cx, y: rect.bottom };
    case "left":
      return { x: rect.left, y: cy };
    case "right":
    default:
      return { x: rect.right, y: cy };
  }
}

function edgePointFromRect(
  rect: DOMRect,
  side: "top" | "bottom" | "left" | "right",
): { x: number; y: number } {
  switch (side) {
    case "top":
      return { x: rect.left + rect.width / 2, y: rect.top };
    case "bottom":
      return { x: rect.left + rect.width / 2, y: rect.bottom };
    case "left":
      return { x: rect.left, y: rect.top + rect.height / 2 };
    case "right":
    default:
      return { x: rect.right, y: rect.top + rect.height / 2 };
  }
}

function viewportCenter(): { x: number; y: number } {
  const pane =
    document.querySelector<HTMLElement>(".react-flow__pane") ??
    document.querySelector<HTMLElement>(".react-flow__viewport");
  if (!pane) {
    return {
      x: globalThis.innerWidth / 2,
      y: globalThis.innerHeight / 2,
    };
  }
  const r = pane.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

export interface PopoverAnchorPosition {
  x: number;
  y: number;
  side: "top" | "bottom" | "left" | "right";
}

/**
 * Resolves a Radix Popover anchor point (viewport px) and which side content opens on.
 */
export function usePopoverPosition(
  anchor: PopoverAnchor,
  preferredSide: "top" | "bottom" | "left" | "right" | undefined,
  /** When set, recomputes `code-line` anchors after Monaco scroll/layout. */
  codeAnchorLayoutEpoch?: number,
): PopoverAnchorPosition {
  const reactFlow = useReactFlow();

  return useMemo(() => {
    const side =
      preferredSide ??
      (anchor.type === "viewport-center" || anchor.type === "coordinates"
        ? "bottom"
        : "right");

    switch (anchor.type) {
      case "node": {
        const el = document.querySelector<HTMLElement>(
          `.react-flow__node[data-id="${safeCssId(anchor.nodeId)}"]`,
        );
        if (!el) return { ...viewportCenter(), side };
        const rect = el.getBoundingClientRect();
        return { ...edgePointFromRect(rect, side), side };
      }
      case "code-line": {
        const marker = document.querySelector<HTMLElement>(
          `[data-walkthrough-code-anchor][data-node-id="${safeCssId(anchor.nodeId)}"][data-line="${anchor.line}"]`,
        );
        if (marker) {
          const r = marker.getBoundingClientRect();
          if (r.width > 0 && r.height > 0) {
            return { ...edgePointFromAnchorRect(r, side), side };
          }
        }
        const el = document.querySelector<HTMLElement>(
          `.react-flow__node[data-id="${safeCssId(anchor.nodeId)}"]`,
        );
        if (!el) return { ...viewportCenter(), side };
        const rect = el.getBoundingClientRect();
        return { ...edgePointFromRect(rect, side), side };
      }
      case "viewport-center":
        return { ...viewportCenter(), side };
      case "coordinates": {
        try {
          const p = reactFlow.flowToScreenPosition({
            x: anchor.x,
            y: anchor.y,
          });
          return { ...p, side };
        } catch {
          return { x: anchor.x, y: anchor.y, side };
        }
      }
      default:
        return { ...viewportCenter(), side: "bottom" };
    }
  }, [anchor, preferredSide, reactFlow, codeAnchorLayoutEpoch]);
}
