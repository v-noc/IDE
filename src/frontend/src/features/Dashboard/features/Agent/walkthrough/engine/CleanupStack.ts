import type { ActionCleanupSink } from "../adapters/actionContext";

/** LIFO teardown queue used by action handlers and the step executor. */
export class CleanupStack implements ActionCleanupSink {
  private fns: Array<() => void> = [];

  push(fn: () => void): void {
    this.fns.push(fn);
  }

  flush(): void {
    while (this.fns.length > 0) {
      const fn = this.fns.pop()!;
      try {
        fn();
      } catch (err) {
        console.error("Walkthrough cleanup error:", err);
      }
    }
  }
}
