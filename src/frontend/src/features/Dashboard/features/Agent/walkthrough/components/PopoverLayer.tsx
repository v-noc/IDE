import { useLayoutEffect, useRef } from "react";

import {
  Popover,
  PopoverAnchor,
  PopoverContent,
} from "@/components/ui/popover";

import {
  usePopoverPosition,
  WALKTHROUGH_POPOVER_GAP,
} from "../hooks/usePopoverPosition";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

const VIEWPORT_CENTER_ANCHOR = { type: "viewport-center" };

export function PopoverLayer() {
  const popover = useWalkthroughStore((s) => s.popover);
  const visible = useWalkthroughStore((s) => s.popoverVisible);
  const visibleText = useWalkthroughStore((s) => s.typewriter.visibleText);
  const isTyping = useWalkthroughStore((s) => s.typewriter.isTyping);
  const codeAnchorLayoutEpoch = useWalkthroughStore(
    (s) => s.codeAnchorLayoutEpoch,
  );

  const anchor = popover?.anchor ?? VIEWPORT_CENTER_ANCHOR;
  const { x, y, side } = usePopoverPosition(
    anchor,
    popover?.side,
    anchor.type === "code-line" ? codeAnchorLayoutEpoch : undefined,
  );

  const scrollRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [visibleText]);

  if (!popover || !visible) return null;

  return (
    <Popover open modal={false} onOpenChange={() => {}}>
      <PopoverAnchor asChild>
        <span
          aria-hidden
          className="pointer-events-none fixed block h-px w-px"
          style={{ left: x, top: y }}
        />
      </PopoverAnchor>
      <PopoverContent
        side={side}
        align="center"
        sideOffset={WALKTHROUGH_POPOVER_GAP}
        collisionPadding={12}
        className="z-[60] flex w-[min(360px,calc(100vw-24px))] min-w-0 max-w-[min(360px,calc(100vw-24px))] flex-col gap-0 overflow-hidden p-0"
        onOpenAutoFocus={(e) => e.preventDefault()}
        onCloseAutoFocus={(e) => e.preventDefault()}
      >
        {popover.title ? (
          <h3 className="walkthrough-popover__title text-popover-foreground shrink-0 border-b px-4 pt-3 pb-2">
            {popover.title}
          </h3>
        ) : null}
        <div
          ref={scrollRef}
          className="min-h-0 max-h-[min(280px,42vh)] overflow-y-auto overflow-x-hidden px-4 py-3"
        >
          <p className="walkthrough-popover__body text-popover-foreground m-0 max-w-full break-words">
            {visibleText}
            {isTyping ? (
              <span className="walkthrough-popover__cursor" aria-hidden>
                ▊
              </span>
            ) : null}
          </p>
        </div>
      </PopoverContent>
    </Popover>
  );
}
