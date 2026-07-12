import type { Estimate, Frame, RunRequest } from "../types";

export interface WalkthroughSource {
  run(
    req: RunRequest,
    onFrame: (frame: Frame) => void,
    signal: AbortSignal,
  ): Promise<void>;
  estimate(req: RunRequest): Promise<Estimate>;
}
