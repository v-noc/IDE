import { ActionHandlerRegistry } from "../actions/ActionHandlerRegistry";
import type { CanvasAdapter } from "../adapters/CanvasAdapter";
import type { WalkthroughStep, WaitAction } from "../types/walkthrough";
import { getDefaultDuration } from "../types/duration";
import { abortableSleep } from "./abortableSleep";
import { CleanupStack } from "./CleanupStack";

const BUFFER_TICK_MS = 48;

export interface StepExecutorContext {
  registry: ActionHandlerRegistry;
  adapter: CanvasAdapter;
  signal: AbortSignal;
  speed: number;
  skipDuration?: boolean;
  /**
   * Called at the authored boundary of each action for timeline UI.
   * `elapsedInAction` is 0 at the action start (timeline frozen here until handler finishes),
   * then advances during the optional buffer phase, then equals `actionDuration` at end.
   */
  onActionProgress?: (actionIndex: number, elapsedInAction: number) => void;
}

export class StepExecutor {
  private readonly cleanupStack = new CleanupStack();

  constructor(
    private readonly step: WalkthroughStep,
    private readonly ctx: StepExecutorContext,
  ) {}

  cleanup(): void {
    this.cleanupStack.flush();
  }

  /** Run all actions with duration pacing. */
  async run(): Promise<void> {
    const n = this.step.actions.length;
    for (let i = 0; i < n; i++) {
      await this.runActionAtIndex(i);
    }
  }

  /**
   * Run actions `0..upToIndex` inclusive. Used for seek fast-path.
   * When `upToIndex < 0`, runs nothing.
   */
  async runUpTo(upToIndex: number): Promise<void> {
    if (upToIndex < 0 || this.step.actions.length === 0) return;
    const last = Math.min(upToIndex, this.step.actions.length - 1);
    for (let i = 0; i <= last; i++) {
      await this.runActionAtIndex(i, true);
    }
  }

  private async runActionAtIndex(
    i: number,
    forceSkipDuration = false,
  ): Promise<void> {
    const { signal, registry, adapter, speed, skipDuration, onActionProgress } =
      this.ctx;
    if (signal.aborted) return;

    const action = this.step.actions[i]!;
    const actionDuration =
      action.type === "wait"
        ? (action as WaitAction).ms
        : (action.duration ?? getDefaultDuration(action.type));

    // Timeline stays at action start until the handler promise settles (freeze during slow work).
    onActionProgress?.(i, 0);

    const handlerStart = performance.now();

    const handler = registry.get(action.type);
    if (handler) {
      await handler(action, {
        adapter,
        signal,
        cleanup: this.cleanupStack,
      });
    }

    if (signal.aborted) return;

    const handlerWallMs = performance.now() - handlerStart;

    const skip = forceSkipDuration || skipDuration;
    if (skip) {
      onActionProgress?.(i, actionDuration);
      return;
    }

    const minWallMs = actionDuration / speed;
    const bufferMs = Math.max(0, minWallMs - handlerWallMs);

    if (bufferMs <= 0) {
      onActionProgress?.(i, actionDuration);
    } else {
      await this.runBufferWithProgress(
        bufferMs,
        signal,
        (frac) => onActionProgress?.(i, frac * actionDuration),
      );
    }
  }

  /** Advance buffer in small ticks so the timeline can move during intentional pacing only. */
  private async runBufferWithProgress(
    bufferMs: number,
    signal: AbortSignal,
    onFrac: (frac: number) => void,
  ): Promise<void> {
    if (bufferMs <= 0) return;

    let elapsed = 0;
    while (elapsed < bufferMs) {
      if (signal.aborted) return;
      const chunk = Math.min(BUFFER_TICK_MS, bufferMs - elapsed);
      await abortableSleep(chunk, signal);
      elapsed += chunk;
      onFrac(Math.min(1, elapsed / bufferMs));
    }
    onFrac(1);
  }
}
