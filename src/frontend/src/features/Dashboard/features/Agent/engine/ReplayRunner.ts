import type { ReplayEvent } from "../types/conversation";
import type { ReplayRegistry } from "./registry";

export type RunnerStatus = "idle" | "running" | "paused" | "stopped";

export interface RunnerCallbacks {
  onStatusChange: (status: RunnerStatus) => void;
  onProgress: (index: number, event: ReplayEvent | null) => void;
  onComplete: () => void;
}

export class ReplayRunner {
  private events: ReplayEvent[] = [];
  private index = 0;
  private status: RunnerStatus = "idle";
  private speed = 1;
  private abortController: AbortController | null = null;
  private registry: ReplayRegistry;
  private callbacks: RunnerCallbacks;

  constructor(registry: ReplayRegistry, callbacks: RunnerCallbacks) {
    this.registry = registry;
    this.callbacks = callbacks;
  }

  load(events: ReplayEvent[]) {
    this.pause();
    this.events = events;
    this.index = 0;
    this.setStatus("idle");
    this.callbacks.onProgress(0, this.events[0] ?? null);
  }

  async play() {
    if (this.status === "running" || this.events.length === 0) return;

    this.abortController = new AbortController();
    this.setStatus("running");
    console.log("events", this.events);
    while (this.index < this.events.length) {
      if (this.abortController.signal.aborted) break;
      const event = this.events[this.index];
      console.log("index", this.index);
      console.log("event", event);
      this.callbacks.onProgress(this.index, event);

      if (this.index > 0) {
        const previous = this.events[this.index - 1];
        const gap = Math.max(0, event.at - previous.at);
        if (gap > 0) {
          await this.sleep(gap / this.speed);
          if (this.abortController.signal.aborted) break;
        }
      }

      const handler = this.registry[event.type];
      if (handler) {
        console.log("handler", event.type);
        await handler(event, this.abortController.signal);
      }

      this.index += 1;
    }

    if (!this.abortController.signal.aborted) {
      this.setStatus("idle");
      this.callbacks.onComplete();
    }
  }

  pause() {
    if (this.status !== "running") return;
    this.abortController?.abort();
    this.setStatus("paused");
  }

  stop() {
    this.abortController?.abort();
    this.index = 0;
    this.setStatus("stopped");
    this.callbacks.onProgress(0, this.events[0] ?? null);
  }

  seek(index: number) {
    if (this.events.length === 0) {
      this.callbacks.onProgress(0, null);
      return;
    }

    this.pause();
    this.index = Math.max(0, Math.min(index, this.events.length - 1));
    this.callbacks.onProgress(this.index, this.events[this.index] ?? null);
  }

  next() {
    if (this.events.length === 0) return;
    if (this.index >= this.events.length - 1) return;
    this.seek(this.index + 1);
  }

  prev() {
    if (this.events.length === 0) return;
    this.seek(this.index - 1);
  }

  setSpeed(speed: number) {
    this.speed = speed;
  }

  private setStatus(status: RunnerStatus) {
    this.status = status;
    this.callbacks.onStatusChange(status);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
      const timer = setTimeout(resolve, ms);
      this.abortController?.signal.addEventListener(
        "abort",
        () => {
          clearTimeout(timer);
          resolve();
        },
        { once: true },
      );
    });
  }
}
