import { useEffect, useEffectEvent } from "react";
import { toast } from "sonner";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { Action } from "../types";
import { useWalkthroughStore } from "../store/useWalkthroughStore";
import { ensureOnCanvas } from "./ensureOnCanvas";
import { getCanvasInstance } from "./canvasRegistry";
import { isNodeFullyInViewport } from "./viewport";
import { queryClient } from "@/lib/queryClient";

function getCanvasSize(): { width: number; height: number } | null {
  const pane = document.querySelector(".react-flow") as HTMLElement | null;
  if (!pane) return null;
  return { width: pane.clientWidth, height: pane.clientHeight };
}

function moveCameraToStep(
  tabId: string,
  nodeId: string,
  isTourRoot: boolean,
  attempts = 0,
) {
  if (useWalkthroughStore.getState().phase !== "playing") return;
  if (attempts > 60) return;

  const instance = getCanvasInstance(tabId);
  if (!instance) return;

  const rfNode = instance.getNode(nodeId);
  if (!rfNode?.measured?.width) {
    requestAnimationFrame(() =>
      moveCameraToStep(tabId, nodeId, isTourRoot, attempts + 1),
    );
    return;
  }

  const width = rfNode.measured.width ?? 0;
  const height = rfNode.measured.height ?? 0;
  const cx = rfNode.position.x + width / 2;
  const cy = rfNode.position.y + height / 2;

  if (isTourRoot) {
    instance.setCenter(cx, cy, { zoom: 1, duration: 500 });
    return;
  }

  const canvas = getCanvasSize();
  const viewport = instance.getViewport();
  if (
    canvas &&
    isNodeFullyInViewport(viewport, canvas, {
      x: rfNode.position.x,
      y: rfNode.position.y,
      width,
      height,
    })
  ) {
    return;
  }

  instance.setCenter(cx, cy, { zoom: instance.getZoom(), duration: 600 });
}

async function runActions(
  tabId: string,
  actions: Action[],
  cursor: number,
) {
  const store = useWalkthroughStore.getState();
  const setSecondarySelectedNode =
    useProjectStore.getState().setSecondarySelectedNode;

  let highlight: { nodeId: string; startLine: number; endLine: number } | null =
    null;
  let codeOpenNodeId: string | null = null;

  for (const action of actions) {
    if (action.type === "select_node") {
      const node = await ensureOnCanvas(queryClient, tabId, action.nodeId, {
        reroot: false,
      });
      if (!node) {
        toast.error(`Could not load node: ${action.nodeId}`);
        return false;
      }
      setSecondarySelectedNode(tabId, node);
      continue;
    }

    if (action.type === "show_code") {
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
      moveCameraToStep(tabId, targetNodeId, cursor === 0);
    }
  }

  return true;
}

/**
 * Reacts to cursor changes and drives canvas actions for the current step.
 */
export function useStepExecutor() {
  const cursor = useWalkthroughStore((s) => s.cursor);
  const phase = useWalkthroughStore((s) => s.phase);
  const tabId = useWalkthroughStore((s) => s.tabId);

  const executeCurrentStep = useEffectEvent(async () => {
    const state = useWalkthroughStore.getState();
    if (!state.tabId || state.cursor < 0) return;

    const step = state.playerSteps[state.cursor];
    if (!step) return;

    useTabStore.getState().setActiveTabId(state.tabId);

    const ok = await runActions(state.tabId, step.actions, state.cursor);
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
