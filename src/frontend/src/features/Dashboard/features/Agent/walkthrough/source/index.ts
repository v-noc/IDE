import { mockSource } from "./mockSource";
import { httpSource } from "./httpSource";
import type { WalkthroughSource } from "./types";

const useMock =
  import.meta.env.VITE_WALKTHROUGH_MOCK !== "0" &&
  import.meta.env.VITE_WALKTHROUGH_MOCK !== "false";

export const walkthroughSource: WalkthroughSource = useMock
  ? mockSource
  : httpSource;

console.info("[walkthrough] source:", useMock ? "mock" : "http");

export { applyFrame, applyOpsToSession } from "./applyFrame";
export type { WalkthroughSource } from "./types";
