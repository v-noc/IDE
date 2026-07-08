import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { queryClient } from "@/lib/queryClient";
import type { ProjectNodeTree } from "@/types/project";
import type { Frame, RunRequest } from "../types";
import type { WalkthroughSource } from "./types";
import {
  buildMockSession,
  buildMockVisitList,
  computeMockEstimate,
  generateMockFrames,
} from "./mockGenerator";

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }

    const timer = window.setTimeout(resolve, ms);
    const onAbort = () => {
      window.clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };

    signal.addEventListener("abort", onAbort, { once: true });
  });
}

function requireProjectContext(req: RunRequest): {
  projectData: ProjectNodeTree;
  projectKey: string;
} {
  const projectData = useProjectStore.getState().projectData;
  if (!projectData?.id || projectData.id !== req.project_id) {
    throw new Error("Project data is not loaded");
  }
  return { projectData, projectKey: projectData.id };
}

export const mockSource: WalkthroughSource = {
  async estimate(req) {
    const { projectData, projectKey } = requireProjectContext(req);
    const visitList = await buildMockVisitList(
      queryClient,
      projectData,
      projectKey,
      req.node_id,
      req.depth,
    );
    return computeMockEstimate(visitList);
  },

  async run(req, onFrame, signal) {
    const { projectData, projectKey } = requireProjectContext(req);
    const visitList = await buildMockVisitList(
      queryClient,
      projectData,
      projectKey,
      req.node_id,
      req.depth,
    );
    const session = buildMockSession(req, visitList);
    const frames = generateMockFrames(session);

    for (const entry of frames) {
      await sleep(entry.delay, signal);
      onFrame(entry.frame as Frame);
    }
  },
};
