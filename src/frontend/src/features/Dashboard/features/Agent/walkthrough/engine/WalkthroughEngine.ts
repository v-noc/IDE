import { ActionHandlerRegistry } from "../actions/ActionHandlerRegistry";
import type { CanvasAdapter } from "../adapters/CanvasAdapter";
import type { WalkthroughStoreApi } from "../store/useWalkthroughStore";
import {
  DEFAULT_POST_POPOVER_PAUSE,
  TYPEWRITER_MS_PER_CHAR,
} from "../types/duration";
import { resolveTimelinePosition } from "../types/resolveTimelinePosition";
import type {
  EngineStatus,
  PopoverConfig,
  StepTimeline,
  Walkthrough,
  WalkthroughStep,
  WalkthroughTimeline,
} from "../types/walkthrough";
import { abortableSleep } from "./abortableSleep";
import { StepExecutor } from "./StepExecutor";
import { TimelineBuilder } from "./TimelineBuilder";

export interface EngineConfig {
  registry: ActionHandlerRegistry;
  adapter: CanvasAdapter;
  store: WalkthroughStoreApi;
}

type InterruptKind = "none" | "pause" | "stop";

/**
 * Orchestrates walkthrough playback: timeline, steps, action pacing, popover typewriter.
 * No React imports — inject {@link WalkthroughStoreApi} for UI sync.
 */
export class WalkthroughEngine {
  private walkthrough: Walkthrough | null = null;
  private timeline: WalkthroughTimeline | null = null;
  private stepIndex = 0;
  private status: EngineStatus = "idle";
  private speed = 1;
  private abortController: AbortController | null = null;
  private elapsedMs = 0;
  private currentExecutor: StepExecutor | null = null;
  private interruptKind: InterruptKind = "none";

  private readonly registry: ActionHandlerRegistry;
  private readonly adapter: CanvasAdapter;
  private readonly store: WalkthroughStoreApi;

  constructor(config: EngineConfig) {
    this.registry = config.registry;
    this.adapter = config.adapter;
    this.store = config.store;
    this.speed = Math.max(0.05, this.store.getState().speed);
  }

  load(walkthrough: Walkthrough): void {
    this.abortController?.abort();
    this.walkthrough = walkthrough;
    this.timeline = TimelineBuilder.build(walkthrough);
    this.stepIndex = 0;
    this.elapsedMs = 0;
    this.currentExecutor?.cleanup();
    this.currentExecutor = null;
    this.interruptKind = "none";

    this.setStatus("idle");
    this.store.getState().setWalkthrough(walkthrough);
    this.store.getState().setTimeline(this.timeline);
    this.store.getState().setElapsedMs(0);
    this.store.getState().setPopover(null);
  }

  async play(): Promise<void> {
    if (this.status === "running") return;
    if (!this.walkthrough || !this.timeline) return;

    if (this.status === "complete") {
      this.stepIndex = 0;
      this.elapsedMs = 0;
      this.store.getState().setElapsedMs(0);
    }

    this.speed = Math.max(0.05, this.store.getState().speed);
    this.interruptKind = "none";
    this.abortController = new AbortController();
    const signal = this.abortController.signal;
    this.setStatus("running");

    try {
      while (this.stepIndex < this.walkthrough.steps.length) {
        if (signal.aborted) break;

        const step = this.walkthrough.steps[this.stepIndex]!;
        const stepTimeline = this.timeline.steps[this.stepIndex]!;
        this.emitStep(step);

        const executor = new StepExecutor(step, {
          registry: this.registry,
          adapter: this.adapter,
          signal,
          speed: this.speed,
          onActionProgress: (actionIndex, elapsedInAction) => {
            const actionMeta = stepTimeline.actions[actionIndex];
            const start = actionMeta?.startMs ?? 0;
            this.elapsedMs = stepTimeline.startMs + start + elapsedInAction;
            this.emitProgress();
          },
        });

        await executor.run();
        this.currentExecutor = executor;

        if (signal.aborted) break;

        if (step.popover) {
          this.emitPopover(step.popover);
          await this.runTypewriter(step.popover.body, stepTimeline, signal);
        }

        if (signal.aborted) break;

        if (step.popover) {
          await abortableSleep(
            DEFAULT_POST_POPOVER_PAUSE / this.speed,
            signal,
          );
        }

        if (signal.aborted) break;

        this.stepIndex += 1;
      }

      if (!signal.aborted) {
        this.setStatus("complete");
        this.clearVisualChrome();
      }
    } finally {
      if (signal.aborted && this.interruptKind === "pause") {
        this.setStatus("paused");
      }
      this.interruptKind = "none";
    }
  }

  pause(): void {
    if (this.status !== "running") return;
    this.interruptKind = "pause";
    this.abortController?.abort();
  }

  stop(): void {
    this.interruptKind = "stop";
    this.abortController?.abort();
    this.currentExecutor?.cleanup();
    this.currentExecutor = null;
    this.stepIndex = 0;
    this.elapsedMs = 0;
    this.store.getState().setElapsedMs(0);
    this.clearVisualChrome();
    this.setStatus("idle");
  }

  async seekToTime(ms: number): Promise<void> {
    if (!this.walkthrough || !this.timeline) return;

    this.interruptKind = "pause";
    this.abortController?.abort();

    const position = resolveTimelinePosition(this.timeline, ms);

    this.currentExecutor?.cleanup();
    this.currentExecutor = null;

    this.store.getState().setPopover(null);

    this.stepIndex = position.stepIndex;
    this.elapsedMs = ms;

    const step = this.walkthrough.steps[this.stepIndex];
    if (!step) return;

    this.emitStep(step);
    const stepTimeline = this.timeline.steps[this.stepIndex]!;

    const upToIndex =
      position.phase === "actions"
        ? (position.actionIndex ?? 0)
        : step.actions.length - 1;

    const executor = new StepExecutor(step, {
      registry: this.registry,
      adapter: this.adapter,
      signal: new AbortController().signal,
      speed: Number.POSITIVE_INFINITY,
      skipDuration: true,
    });

    await executor.runUpTo(upToIndex);
    this.currentExecutor = executor;

    if (position.phase === "typewriter" && step.popover) {
      this.emitPopover(step.popover);
      this.store.getState().setTypewriter({
        fullText: step.popover.body,
        visibleText: step.popover.body.slice(0, position.charIndex ?? 0),
        charIndex: position.charIndex ?? 0,
        isTyping: false,
      });
    }

    if (position.phase === "post-pause" && step.popover) {
      this.emitPopover(step.popover);
      this.store.getState().setTypewriter({
        fullText: step.popover.body,
        visibleText: step.popover.body,
        charIndex: step.popover.body.length,
        isTyping: false,
      });
    }

    this.emitProgress();
    this.setStatus("paused");
  }

  async seekToStep(stepId: string): Promise<void> {
    if (!this.walkthrough || !this.timeline) return;
    const idx = this.walkthrough.steps.findIndex((s) => s.id === stepId);
    if (idx < 0) return;
    const start = this.timeline.steps[idx]?.startMs ?? 0;
    await this.seekToTime(start);
  }

  async next(): Promise<void> {
    if (!this.walkthrough || !this.timeline) return;
    const nextIdx = Math.min(
      this.stepIndex + 1,
      this.walkthrough.steps.length - 1,
    );
    const start = this.timeline.steps[nextIdx]?.startMs ?? 0;
    await this.seekToTime(start);
  }

  async prev(): Promise<void> {
    if (!this.timeline) return;
    const prevIdx = Math.max(this.stepIndex - 1, 0);
    const start = this.timeline.steps[prevIdx]?.startMs ?? 0;
    await this.seekToTime(start);
  }

  setSpeed(speed: number): void {
    this.speed = Math.max(0.05, speed);
    this.store.getState().setSpeed(this.speed);
  }

  destroy(): void {
    this.stop();
    this.walkthrough = null;
    this.timeline = null;
  }

  getStepIndex(): number {
    return this.stepIndex;
  }

  getElapsedMs(): number {
    return this.elapsedMs;
  }

  getStatus(): EngineStatus {
    return this.status;
  }

  private async runTypewriter(
    text: string,
    stepTimeline: StepTimeline,
    signal: AbortSignal,
  ): Promise<void> {
    const totalChars = text.length;
    const msPerChar = TYPEWRITER_MS_PER_CHAR / this.speed;

    this.store.getState().resetTypewriter(text);

    for (let i = 0; i <= totalChars; i++) {
      if (signal.aborted) break;

      this.store.getState().setTypewriter({
        charIndex: i,
        visibleText: text.slice(0, i),
        isTyping: i < totalChars,
      });

      this.elapsedMs =
        stepTimeline.startMs +
        stepTimeline.actionsDuration +
        i * TYPEWRITER_MS_PER_CHAR;
      this.emitProgress();

      if (i < totalChars) {
        await abortableSleep(msPerChar, signal);
      }
    }
  }

  private emitStep(step: WalkthroughStep): void {
    this.store.getState().setCurrentStep(this.stepIndex, step.id);
  }

  private emitPopover(config: PopoverConfig): void {
    this.store.getState().setPopover(config);
  }

  private emitProgress(): void {
    this.store.getState().setElapsedMs(this.elapsedMs);
  }

  private setStatus(status: EngineStatus): void {
    this.status = status;
    this.store.getState().setStatus(status);
  }

  /** Clears popover, spotlight, code highlights, and forced code panels. */
  private clearVisualChrome(): void {
    this.store.getState().setPopover(null);
    this.store.getState().setSpotlightNodeId(null);
    this.store.getState().clearHighlightStore();
    this.store.getState().clearForcedCodeOpen();
  }
}
