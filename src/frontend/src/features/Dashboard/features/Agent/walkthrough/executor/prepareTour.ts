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
  const failedIds: string[] = [];

  for (const visit of session.visit_list.nodes) {
    try {
      const node = await ensureOnCanvas(queryClient, tabId, visit.node_id);
      if (!node) {
        failedIds.push(visit.node_id);
      }
    } catch {
      failedIds.push(visit.node_id);
    }
  }

  const stopIds = session.visit_list.nodes.map((visit) => visit.node_id);
  if (stopIds.length > 0) {
    useProjectStore.getState().expandNodesBulk(tabId, stopIds);
  }

  const rootId = session.visit_list.nodes[0]?.node_id;
  if (rootId) {
    try {
      await ensureOnCanvas(queryClient, tabId, rootId);
    } catch {
      // best-effort restore focus to tour root
    }
  }

  if (failedIds.length > 0) {
    toast.error(`${failedIds.length} stops could not be loaded`);
  }
}
