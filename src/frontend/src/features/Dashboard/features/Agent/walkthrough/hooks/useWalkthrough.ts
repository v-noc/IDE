import { useEffect, useMemo, useRef } from "react";
import { useReactFlow } from "@xyflow/react";
import { createDefaultRegistry } from "../actions/createDefaultRegistry";
import { ReactFlowCanvasAdapter } from "../adapters/ReactFlowCanvasAdapter";
import { WalkthroughEngine } from "../engine/WalkthroughEngine";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import {
  useWalkthroughStore,
  type WalkthroughControls,
} from "../store/useWalkthroughStore";
import type { Walkthrough } from "../types/walkthrough";

/**
 * Builds engine + adapter for the canvas tab. Must run under ReactFlowProvider.
 */
export function useWalkthrough(canvasTabId: string): WalkthroughControls {
  const reactFlow = useReactFlow();
  const engineRef = useRef<WalkthroughEngine | null>(null);

  const registry = useMemo(() => createDefaultRegistry(), []);

  const adapter = useMemo(
    () =>
      new ReactFlowCanvasAdapter(
        () => canvasTabId,
        () => reactFlow,
        useProjectStore,
        useTabStore,
        useWalkthroughStore,
      ),
    [canvasTabId, reactFlow],
  );

  useEffect(() => {
    const engine = new WalkthroughEngine({
      registry,
      adapter,
      store: useWalkthroughStore,
    });
    engineRef.current = engine;
    return () => engine.destroy();
  }, [registry, adapter]);

  const speed = useWalkthroughStore((s) => s.speed);
  useEffect(() => {
    engineRef.current?.setSpeed(speed);
  }, [speed]);

  return useMemo(
    (): WalkthroughControls => ({
      load: (walkthrough: Walkthrough) => {
        engineRef.current?.load(walkthrough);
      },
      play: () => engineRef.current?.play() ?? Promise.resolve(),
      pause: () => engineRef.current?.pause(),
      stop: () => engineRef.current?.stop(),
      next: () => engineRef.current?.next() ?? Promise.resolve(),
      prev: () => engineRef.current?.prev() ?? Promise.resolve(),
      seekToStep: (stepId: string) =>
        engineRef.current?.seekToStep(stepId) ?? Promise.resolve(),
      seekToTime: (ms: number) =>
        engineRef.current?.seekToTime(ms) ?? Promise.resolve(),
      setSpeed: (s: number) => engineRef.current?.setSpeed(s),
    }),
    [],
  );
}
