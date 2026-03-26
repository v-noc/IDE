import { ActionHandlerRegistry } from "../actions/ActionHandlerRegistry";
import type { CanvasAdapter } from "../adapters/CanvasAdapter";
import type { WalkthroughStep, WaitAction } from "../types/walkthrough";
import { getDefaultDuration } from "../types/duration";
import { abortableSleep } from "./abortableSleep";
import { CleanupStack } from "./CleanupStack";

export interface StepExecutorContext {
  registry: ActionHandlerRegistry;
  adapter: CanvasAdapter;
  signal: AbortSignal;
  speed: number;
  skipDuration?: boolean;
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

    const startTime = performance.now();

    const handler = registry.get(action.type);
    if (handler) {
      await handler(action, {
        adapter,
        signal,
        cleanup: this.cleanupStack,
      });
    }

    if (signal.aborted) return;

    const skip = forceSkipDuration || skipDuration;
    if (!skip) {
      const elapsed = performance.now() - startTime;
      const remaining = actionDuration / speed - elapsed;
      if (remaining > 0) {
        await abortableSleep(remaining, signal);
      }
    }

    onActionProgress?.(i, actionDuration);
  }
}
