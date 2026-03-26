import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { usePopoverPosition } from "../hooks/usePopoverPosition";
import type { PopoverAnchor } from "../types/walkthrough";

const VIEWPORT_CENTER_ANCHOR: PopoverAnchor = { type: "viewport-center" };

export function PopoverLayer() {
  const popover = useWalkthroughStore((s) => s.popover);
  const visible = useWalkthroughStore((s) => s.popoverVisible);
  const visibleText = useWalkthroughStore((s) => s.typewriter.visibleText);
  const isTyping = useWalkthroughStore((s) => s.typewriter.isTyping);

  const position = usePopoverPosition(
    popover?.anchor ?? VIEWPORT_CENTER_ANCHOR,
    popover?.side,
  );

  if (!popover || !visible) return null;

  return (
    <div
      className="walkthrough-popover"
      style={{
        position: "fixed",
        left: position.x,
        top: position.y,
        transform: "translate(-50%, -50%)",
      }}
    >
      {popover.title ? (
        <h3 className="walkthrough-popover__title">{popover.title}</h3>
      ) : null}
      <div className="walkthrough-popover__body">
        {visibleText}
        {isTyping ? (
          <span className="walkthrough-popover__cursor" aria-hidden>
            ▊
          </span>
        ) : null}
      </div>
    </div>
  );
}
