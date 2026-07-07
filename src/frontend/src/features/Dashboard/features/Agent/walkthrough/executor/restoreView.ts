import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
import type { SavedView } from "../types";

export function captureSavedView(tabId: string): SavedView {
  const store = useProjectStore.getState();
  return {
    tabId,
    selectedNodeId: store.selectedNode[tabId]?.id ?? null,
    secondarySelectedNodeId: store.secondarySelectedNode[tabId]?.id ?? null,
    expandedNodeIds: [...(store.expandedNodeIds[tabId] ?? [])],
    focusStack: (store.focusStack[tabId] ?? []).map((node) => node.id),
  };
}

export function restoreSavedView(view: SavedView) {
  const projectData = useProjectStore.getState().projectData;
  if (!projectData) return;

  const { tabId } = view;

  useProjectStore.setState((state) => {
    state.expandedNodeIds[tabId] = [...view.expandedNodeIds];
  });

  const store = useProjectStore.getState();
  store.clearFocus(tabId);

  const focusNodes = view.focusStack
    .map((id) => findNodeByKey(projectData, id))
    .filter((node): node is NonNullable<typeof node> => node != null);

  if (focusNodes.length > 0) {
    store.pushFocusBulk(tabId, focusNodes);
  }

  const selected = view.selectedNodeId
    ? findNodeByKey(projectData, view.selectedNodeId)
    : null;
  store.setSelectedNode(tabId, selected ?? null);

  const secondary = view.secondarySelectedNodeId
    ? findNodeByKey(projectData, view.secondarySelectedNodeId)
    : null;
  store.setSecondarySelectedNode(tabId, secondary ?? null);
}
