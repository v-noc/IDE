import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { OutlineRow } from "./OutlineRow";
import { jumpToVisit } from "../store/useWalkthroughStore";

export function TourOutline() {
  const [session, playerSteps, cursor, jumpTo] = useWalkthroughStore(
    useShallow((state) => [
      state.session,
      state.playerSteps,
      state.cursor,
      state.jumpTo,
    ]),
  );

  const currentVisitOrder = useMemo(() => {
    if (cursor < 0 || !playerSteps[cursor]) return null;
    return playerSteps[cursor].visitOrder;
  }, [cursor, playerSteps]);

  if (!session) {
    return (
      <p className="rounded-md border border-dashed border-border p-3 text-xs text-muted-foreground">
        Generate a walkthrough to see the tour outline.
      </p>
    );
  }

  const stepsByOrder = new Map(
    session.node_steps.map((nodeSteps) => [nodeSteps.order, nodeSteps]),
  );

  return (
    <section className="space-y-1">
      <p className="px-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        Tour outline
      </p>
      <div className="max-h-64 space-y-0.5 overflow-auto rounded-md border border-border p-1">
        {session.visit_list.nodes.map((visit) => (
          <OutlineRow
            key={`${visit.order}-${visit.node_id}`}
            visit={visit}
            nodeSteps={stepsByOrder.get(visit.order)}
            isCurrent={visit.order === currentVisitOrder}
            onJump={jumpTo}
            onJumpVisit={jumpToVisit}
          />
        ))}
      </div>
    </section>
  );
}
