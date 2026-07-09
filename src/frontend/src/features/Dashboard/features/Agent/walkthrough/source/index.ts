import { httpSource } from "./httpSource";

export const walkthroughSource = httpSource;
console.info("[walkthrough] source: http (backend)");

export { applyFrame, applyOpsToSession } from "./applyFrame";
export type { WalkthroughSource } from "./types";
