import type { ReactFlowInstance } from "@xyflow/react";

const registry = new Map<string, ReactFlowInstance>();

export function registerCanvas(tabId: string, instance: ReactFlowInstance) {
  registry.set(tabId, instance);
}

export function unregisterCanvas(tabId: string) {
  registry.delete(tabId);
}

export function getCanvasInstance(tabId: string): ReactFlowInstance | null {
  return registry.get(tabId) ?? null;
}
