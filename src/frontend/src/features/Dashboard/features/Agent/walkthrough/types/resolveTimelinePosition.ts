import { TYPEWRITER_MS_PER_CHAR } from "./duration";
import type { TimelinePosition, WalkthroughTimeline } from "./walkthrough";

/**
 * Map absolute timeline time (ms) to step phase, action index, or typewriter char.
 */
export function resolveTimelinePosition(
  timeline: WalkthroughTimeline,
  timeMs: number,
): TimelinePosition {
  if (timeline.steps.length === 0) {
    return { stepIndex: 0, phase: "post-pause" };
  }

  const t = Math.max(0, Math.min(timeMs, timeline.totalDuration));

  const step = timeline.steps.find((s) => t >= s.startMs && t < s.endMs);
  if (!step) {
    const last = timeline.steps[timeline.steps.length - 1]!;
    return { stepIndex: last.stepIndex, phase: "post-pause" };
  }

  const elapsed = t - step.startMs;

  if (elapsed < step.actionsDuration) {
    const action = step.actions.find((a) => elapsed >= a.startMs && elapsed < a.endMs);
    const actionIndex =
      action?.actionIndex ??
      (step.actions.length > 0 ? step.actions[step.actions.length - 1]!.actionIndex : 0);
    const startMs = action?.startMs ?? 0;
    return {
      stepIndex: step.stepIndex,
      phase: "actions",
      actionIndex,
      actionElapsedMs: elapsed - startMs,
    };
  }

  const typewriterStart = step.actionsDuration;
  if (elapsed < typewriterStart + step.typewriterDuration) {
    const typewriterElapsed = elapsed - typewriterStart;
    const charIndex = Math.floor(typewriterElapsed / TYPEWRITER_MS_PER_CHAR);
    return { stepIndex: step.stepIndex, phase: "typewriter", charIndex };
  }

  return { stepIndex: step.stepIndex, phase: "post-pause" };
}
