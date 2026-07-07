import smallFunctionFixture from "../fixtures/smallFunction.json";
import classWithCallFixture from "../fixtures/classWithCall.json";
import type { Estimate, Frame, MockFixture, RunRequest } from "../types";
import { mockFixtureSchema } from "../types";
import type { WalkthroughSource } from "./types";

const FIXTURES: Record<string, MockFixture> = {
  smallFunction: mockFixtureSchema.parse(smallFunctionFixture),
  classWithCall: mockFixtureSchema.parse(classWithCallFixture),
};

function pickFixture(req: RunRequest): MockFixture {
  // Use the richer fixture when depth > 0; otherwise the minimal tour.
  return req.depth > 0 ? FIXTURES.classWithCall : FIXTURES.smallFunction;
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }

    const timer = window.setTimeout(resolve, ms);
    const onAbort = () => {
      window.clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };

    signal.addEventListener("abort", onAbort, { once: true });
  });
}

export const mockSource: WalkthroughSource = {
  async estimate(req) {
    return pickFixture(req).estimate;
  },

  async run(req, onFrame, signal) {
    const fixture = pickFixture(req);

    for (const entry of fixture.frames) {
      await sleep(entry.delay, signal);
      onFrame(entry.frame as Frame);
    }
  },
};
