import {
  DEFAULT_POST_POPOVER_PAUSE,
  TYPEWRITER_MS_PER_CHAR,
  getDefaultDuration,
} from "../types/duration";
import type {
  ActionTimeline,
  StepTimeline,
  WaitAction,
  Walkthrough,
  WalkthroughTimeline,
} from "../types/walkthrough";

export class TimelineBuilder {
  static build(walkthrough: Walkthrough): WalkthroughTimeline {
    let cursor = 0;
    const steps: StepTimeline[] = [];

    for (let i = 0; i < walkthrough.steps.length; i++) {
      const step = walkthrough.steps[i]!;
      const stepStart = cursor;

      let actionCursor = 0;
      const actions: ActionTimeline[] = step.actions.map((action, j) => {
        const duration =
          action.type === "wait"
            ? (action as WaitAction).ms
            : (action.duration ?? getDefaultDuration(action.type));

        const entry: ActionTimeline = {
          actionIndex: j,
          startMs: actionCursor,
          endMs: actionCursor + duration,
          duration,
        };
        actionCursor += duration;
        return entry;
      });

      const actionsDuration = actionCursor;

      const typewriterDuration = step.popover
        ? step.popover.body.length * TYPEWRITER_MS_PER_CHAR
        : 0;

      const postPause = step.popover ? DEFAULT_POST_POPOVER_PAUSE : 0;

      const totalStepDuration =
        actionsDuration + typewriterDuration + postPause;

      steps.push({
        stepIndex: i,
        stepId: step.id,
        startMs: stepStart,
        endMs: stepStart + totalStepDuration,
        actionsDuration,
        typewriterDuration,
        actions,
      });

      cursor += totalStepDuration;
    }

    return { totalDuration: cursor, steps };
  }
}
