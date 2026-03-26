import { useMemo } from "react";
import { useReactFlow } from "@xyflow/react";
import type { PopoverAnchor } from "../types/walkthrough";

const GAP = 12;

function safeCssId(id: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(id);
  }
  return id.replace(/["\\]/g, "\\$&");
}

function offsetFromRect(
  rect: DOMRect,
  side: "top" | "bottom" | "left" | "right",
): { x: number; y: number } {
  switch (side) {
    case "top":
      return { x: rect.left + rect.width / 2, y: rect.top - GAP };
    case "bottom":
      return { x: rect.left + rect.width / 2, y: rect.bottom + GAP };
    case "left":
      return { x: rect.left - GAP, y: rect.top + rect.height / 2 };
    case "right":
    default:
      return { x: rect.right + GAP, y: rect.top + rect.height / 2 };
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

/**
 * Resolves popover anchor to viewport coordinates (absolute positioning).
 */
export function usePopoverPosition(
  anchor: PopoverAnchor,
  preferredSide: "top" | "bottom" | "left" | "right" | undefined,
): { x: number; y: number } {
  const reactFlow = useReactFlow();

  return useMemo(() => {
    const side = preferredSide ?? "right";

    switch (anchor.type) {
      case "node": {
        const el = document.querySelector<HTMLElement>(
          `.react-flow__node[data-id="${safeCssId(anchor.nodeId)}"]`,
        );
        if (!el) return viewportCenter();
        const rect = el.getBoundingClientRect();
        return offsetFromRect(rect, side);
      }
      case "code-line": {
        const el = document.querySelector<HTMLElement>(
          `.react-flow__node[data-id="${safeCssId(anchor.nodeId)}"]`,
        );
        if (!el) return viewportCenter();
        const rect = el.getBoundingClientRect();
        return offsetFromRect(rect, side);
      }
      case "viewport-center":
        return viewportCenter();
      case "coordinates": {
        try {
          const p = reactFlow.flowToScreenPosition({
            x: anchor.x,
            y: anchor.y,
          });
          return p;
        } catch {
          return { x: anchor.x, y: anchor.y };
        }
      }
      default:
        return viewportCenter();
    }
  }, [anchor, preferredSide, reactFlow]);
}
