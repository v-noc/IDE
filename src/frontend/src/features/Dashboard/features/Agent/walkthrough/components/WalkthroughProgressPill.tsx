import { Button } from "@/components/ui/button";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";

export function WalkthroughProgressPill() {
  const [playerSteps, cursor, exit] = useWalkthroughStore(
    useShallow((state) => [state.playerSteps, state.cursor, state.exit]),
  );

  const step = cursor >= 0 ? playerSteps[cursor] : null;
  const position = cursor >= 0 ? cursor + 1 : 0;
  const total = playerSteps.length;

  return (
    <div className="pointer-events-auto flex h-10 items-center gap-3 rounded-full border border-border bg-background/95 px-4 text-sm shadow-md backdrop-blur">
      <span className="font-medium text-foreground">
        {step?.title ?? "Walkthrough"}
      </span>
      <span className="text-xs text-muted-foreground">
        {position} / {total || "…"}
      </span>
      <Button type="button" variant="ghost" size="sm" className="h-7 px-2" onClick={exit}>
        Exit
      </Button>
    </div>
  );
}
