import type { ReplayEvent } from "../../types/conversation";

export async function waitHandler(
  event: ReplayEvent,
  signal: AbortSignal,
): Promise<void> {
  const duration =
    event.type === "wait" && typeof event.payload.ms === "number"
      ? event.payload.ms
      : 0;

  if (signal.aborted) return;

  await new Promise<void>((resolve) => {
    const onAbort = () => {
      clearTimeout(timer);
      resolve();
    };
    const timer = setTimeout(() => {
      signal.removeEventListener("abort", onAbort);
      resolve();
    }, duration);

    signal.addEventListener("abort", onAbort, { once: true });
  });
}
