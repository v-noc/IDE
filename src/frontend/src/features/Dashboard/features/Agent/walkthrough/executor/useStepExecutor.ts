import { useEffect, useEffectEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { Action } from "../types";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { ensureOnCanvas } from "./ensureOnCanvas";
import { getCanvasInstance } from "./canvasRegistry";

function panToNode(tabId: string, nodeId: string) {
  const instance = getCanvasInstance(tabId);
  if (!instance) return;

  const rfNode = instance.getNode(nodeId);
  if (!rfNode?.measured?.width) {
    requestAnimationFrame(() => panToNode(tabId, nodeId));
    return;
  }

  instance.setCenter(
    rfNode.position.x + (rfNode.measured.width ?? 0) / 2,
    rfNode.position.y + (rfNode.measured.height ?? 0) / 2,
    { zoom: 1, duration: 500 },
  );
}

async function runActions(
  tabId: string,
  actions: Action[],
  queryClient: ReturnType<typeof useQueryClient>,
) {
  const store = useWalkthroughStore.getState();
  const handleNodeSelection = useTabStore.getState().handleNodeSelection;
  const expandNode = useProjectStore.getState().expandNode;

  let highlight: { nodeId: string; startLine: number; endLine: number } | null =
    null;
  let codeOpenNodeId: string | null = null;

  for (const action of actions) {
    if (action.type === "select_node") {
      const node = await ensureOnCanvas(queryClient, tabId, action.nodeId);
      if (!node) {
        toast.error(`Could not load node: ${action.nodeId}`);
        return false;
      }
      handleNodeSelection(tabId, node, "primary");
      continue;
    }

    if (action.type === "show_code") {
      expandNode(tabId, action.nodeId);
      codeOpenNodeId = action.nodeId;
      continue;
    }

    if (action.type === "highlight_lines") {
      highlight = {
        nodeId: action.nodeId,
        startLine: action.startLine,
        endLine: action.endLine,
      };
    }
  }

  store.setHighlight(highlight);
  store.setCodeOpenNodeId(codeOpenNodeId);

  if (!store.userInteracted) {
    const targetNodeId =
      highlight?.nodeId ??
      actions.find((a) => a.type === "select_node")?.nodeId ??
      actions.find((a) => a.type === "show_code")?.nodeId;

    if (targetNodeId) {
      panToNode(tabId, targetNodeId);
    }
  }

  return true;
}

/**
 * Reacts to cursor changes and drives canvas actions for the current step.
 */
export function useStepExecutor() {
  const queryClient = useQueryClient();
  const cursor = useWalkthroughStore((s) => s.cursor);
  const phase = useWalkthroughStore((s) => s.phase);
  const tabId = useWalkthroughStore((s) => s.tabId);

  const executeCurrentStep = useEffectEvent(async () => {
    const state = useWalkthroughStore.getState();
    if (!state.tabId || state.cursor < 0) return;

    const step = state.playerSteps[state.cursor];
    if (!step) return;

    useTabStore.getState().setActiveTabId(state.tabId);

    const ok = await runActions(state.tabId, step.actions, queryClient);
    if (!ok) return;
  });

  useEffect(() => {
    if (phase !== "playing") return;
    void executeCurrentStep();
  }, [cursor, phase, executeCurrentStep]);

  useEffect(() => {
    if (!tabId) return;
    return () => {
      useWalkthroughStore.getState().clearHighlight();
    };
  }, [tabId]);
}
