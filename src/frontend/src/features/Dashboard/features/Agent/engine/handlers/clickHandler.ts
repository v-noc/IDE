import type { ReplayEvent } from "../../types/conversation";

export async function clickHandler(
  _event: ReplayEvent,
  signal: AbortSignal,
): Promise<void> {
  if (signal.aborted) return;

  await new Promise<void>((resolve) => {
    const onAbort = () => {
      clearTimeout(timer);
      resolve();
    };
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort);
      resolve();
    }, 200);

    signal.addEventListener("abort", onAbort, { once: true });
  });
}
