import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { codeApi } from "@/services/code/api";
import type { ProjectNodeTree } from "@/types/project";
import { resolveLineageFromPath } from "@/features/Dashboard/utils/resolveLineageFromPath";
import {
  pickFocusNodeIdFromSearchParams,
  stripFocusSearchParams,
} from "@/features/Dashboard/utils/shareUrl";

/**
 * On `/project/:id?focus=…` or `?share=…`, resolve server lineage, focus stack + selection on the root tab (same pattern as call explore).
 */
export function useDashboardDeepLinkFocus(projectIdFromRoute: string | undefined) {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const projectData = useProjectStore((s) => s.projectData);
  const seqRef = useRef(0);

  const focusRaw =
    searchParams.get("focus") ?? searchParams.get("share") ?? "";

  useEffect(() => {
    if (!focusRaw || !projectIdFromRoute) return;
    const projectKey = `ProjectSchema/${projectIdFromRoute}`;
    if (!projectData || projectData.id !== projectKey) return;

    const targetId = pickFocusNodeIdFromSearchParams(searchParams);
    if (!targetId) {
      setSearchParams((prev) => stripFocusSearchParams(prev), { replace: true });
      return;
    }

    const mySeq = ++seqRef.current;
    const rootTabId = useTabStore.getState().rootTabId;

    void (async () => {
      try {
        const { path_ids } = await codeApi.getLineage(projectKey, targetId);
        if (mySeq !== seqRef.current) return;
        if (!path_ids?.length) return;

        const pd = useProjectStore.getState().projectData;
        if (!pd || pd.id !== projectKey || mySeq !== seqRef.current) return;

        const lineage = await resolveLineageFromPath(
          queryClient,
          pd as ProjectNodeTree,
          projectKey,
          path_ids,
        );
        if (mySeq !== seqRef.current) return;
        if (!lineage?.length) return;

        const fullTarget = lineage[lineage.length - 1];
        useTabStore.getState().setActiveTabId(rootTabId);
        const ps = useProjectStore.getState();
        ps.clearFocus(rootTabId);
        ps.pushFocusBulk(rootTabId, lineage);
        ps.setSelectedNode(rootTabId, fullTarget);
        ps.expandNodesBulk(rootTabId, lineage.map((n) => n.id));
      } catch {
        /* ignore */
      } finally {
        if (mySeq === seqRef.current) {
          setSearchParams((prev) => stripFocusSearchParams(prev), { replace: true });
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- async reads latest store; `projectData?.id` gates load
  }, [
    focusRaw,
    projectData?.id,
    projectIdFromRoute,
    queryClient,
    searchParams,
    setSearchParams,
  ]);
}
