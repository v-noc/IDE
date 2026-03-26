import type { ActionHandler } from "../adapters/actionContext";
import type { Action } from "../types/walkthrough";

export class ActionHandlerRegistry {
  private handlers = new Map<string, ActionHandler>();

  register<T extends Action>(
    type: T["type"],
    handler: ActionHandler<T>,
  ): this {
    this.handlers.set(type, handler as ActionHandler);
    return this;
  }

  get(type: string): ActionHandler | undefined {
    return this.handlers.get(type);
  }

  has(type: string): boolean {
    return this.handlers.has(type);
  }
}
