import type { QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { WalkthroughSession } from "../types";
import { ensureOnCanvas } from "./ensureOnCanvas";

export async function prepareTour(
  queryClient: QueryClient,
  tabId: string,
  session: WalkthroughSession,
): Promise<void> {
  const visits = session.visit_list.nodes;
  if (visits.length === 0) return;

  const failedIds: string[] = [];

  try {
    const root = await ensureOnCanvas(
      queryClient,
      tabId,
      visits[0].node_id,
      { reroot: true },
    );
    if (!root) {
      failedIds.push(visits[0].node_id);
    }
  } catch {
    failedIds.push(visits[0].node_id);
  }

  for (const visit of visits.slice(1)) {
    try {
      const node = await ensureOnCanvas(queryClient, tabId, visit.node_id, {
        reroot: false,
      });
      if (!node) {
        failedIds.push(visit.node_id);
      }
    } catch {
      failedIds.push(visit.node_id);
    }
  }

  const stopIds = visits.map((visit) => visit.node_id);
  useProjectStore.getState().expandNodesBulk(tabId, stopIds);

  if (failedIds.length > 0) {
    toast.error(`${failedIds.length} stops could not be loaded`);
  }
}
