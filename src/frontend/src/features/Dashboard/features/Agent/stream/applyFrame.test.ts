import { describe, expect, it } from "vitest";
import { applyFrame, applyOps } from "./applyFrame";
import { parseNdjsonChunk } from "./source";
import type { MirrorEntry } from "./applyFrame";

describe("applyOps append", () => {
  it("concatenates string deltas before standard patches", () => {
    const snapshot = {
      messages: [{ parts: [{ type: "text", text: "Hel" }] }],
    };
    const next = applyOps(snapshot, [
      { op: "append", path: "/messages/0/parts/0/text", value: "lo" },
      { op: "replace", path: "/messages/0/parts/0/type", value: "text" },
    ]) as typeof snapshot;

    expect(next.messages[0]!.parts[0]!.text).toBe("Hello");
  });
});

describe("applyFrame", () => {
  it("opens, patches with seq guard, and closes", () => {
    let docs: Record<string, MirrorEntry> = {};
    docs = applyFrame(
      {
        kind: "open",
        doc: "ConversationSchema/c1",
        snapshot: { id: "ConversationSchema/c1", messages: [] },
      },
      docs,
    );
    expect(docs["ConversationSchema/c1"]?.lastSeq).toBe(-1);
    expect(docs["ConversationSchema/c1"]?.status).toBe("open");

    docs = applyFrame(
      {
        kind: "patch",
        doc: "ConversationSchema/c1",
        seq: 0,
        ops: [
          {
            op: "add",
            path: "/messages/-",
            value: { id: "m1", role: "user", parts: [] },
          },
        ],
      },
      docs,
    );
    expect(docs["ConversationSchema/c1"]?.lastSeq).toBe(0);

    // stale
    const before = docs;
    docs = applyFrame(
      {
        kind: "patch",
        doc: "ConversationSchema/c1",
        seq: 0,
        ops: [{ op: "replace", path: "/title", value: "nope" }],
      },
      docs,
    );
    expect(docs).toBe(before);

    docs = applyFrame(
      {
        kind: "close",
        doc: "ConversationSchema/c1",
        status: "idle",
      },
      docs,
    );
    expect(docs["ConversationSchema/c1"]?.status).toBe("closed");
  });
});

describe("parseNdjsonChunk", () => {
  it("parses open/patch/close and skips garbage", () => {
    const frames: unknown[] = [];
    const chunk =
      '{"kind":"open","doc":"c1","snapshot":{"id":"c1"}}\n' +
      "GARBAGE\n" +
      '{"kind":"patch","doc":"c1","seq":0,"ops":[{"op":"replace","path":"/title","value":"hi"}]}\n' +
      '{"kind":"close","doc":"c1","status":"idle"}\n';

    parseNdjsonChunk(chunk, (frame) => {
      frames.push(frame);
    });

    expect(frames).toHaveLength(3);
    expect(frames[0]).toMatchObject({ kind: "open", doc: "c1" });
    expect(frames[2]).toMatchObject({ kind: "close", status: "idle" });
  });
});
