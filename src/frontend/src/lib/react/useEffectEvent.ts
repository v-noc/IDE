import * as React from "react";

type AnyFn = (...args: never[]) => unknown;

/**
 * React 19.2+ `useEffectEvent`: stable callback that always sees latest props/state.
 * Falls back to ref + `useCallback` on older React (same contract).
 */
export function useEffectEvent<T extends AnyFn>(fn: T): T {
  const R = React as unknown as {
    useEffectEvent?: <F extends AnyFn>(callback: F) => F;
  };
  if (typeof R.useEffectEvent === "function") {
    return R.useEffectEvent(fn);
  }
  const ref = React.useRef(fn);
  React.useInsertionEffect(() => {
    ref.current = fn;
  });
  return React.useCallback(((...args: never[]) =>
    ref.current(...args)) as T, []);
}
