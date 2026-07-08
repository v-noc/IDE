import { describe, expect, it } from "vitest";
import { applyFrame } from "../source/applyFrame";
import { parseNdjsonChunk } from "../source/httpSource";
import { visitNodeSchema } from "../types";

describe("applyFrame end frame", () => {
  it("keeps playing phase when generation completes during playback", () => {
    const result = applyFrame(
      { kind: "end", status: "complete" },
      {
        session: null,
        lastSeq: 3,
        phase: "playing",
      },
    );

    expect(result.phase).toBe("playing");
  });
});

describe("visitNodeSchema", () => {
  it("accepts project stops", () => {
    const parsed = visitNodeSchema.parse({
      node_id: "project-1",
      name: "My Project",
      qname: null,
      node_type: "project",
      description: "Root project",
      level: 0,
      order: 0,
      parent_order: null,
      target_id: null,
      mode: "full",
      first_seen_order: null,
      has_code: false,
      start_line: null,
      end_line: null,
      line_count: null,
      gated: false,
    });

    expect(parsed.node_type).toBe("project");
  });
});

describe("parseNdjsonChunk", () => {
  it("skips malformed lines and keeps valid frames", () => {
    const frames: unknown[] = [];
    const chunk =
      '{"kind":"hello","protocol":1,"session":{"id":"x","created_at":"t","request":{"project_id":"p","node_id":"n","depth":0},"branch":"main","commit_id":"c","visit_list":{"start_node_id":"n","depth":0,"nodes":[]},"node_steps":[],"status":"generating","error_log":[],"schema_version":"1","prompt_version":"1","model_id":"m","usage":{"prompt_tokens":0,"completion_tokens":0}}}\n' +
      "GARBAGE\n" +
      '{"kind":"end","status":"complete"}\n';

    parseNdjsonChunk(chunk, (frame) => {
      frames.push(frame);
    });

    expect(frames).toHaveLength(2);
    expect(frames[0]).toMatchObject({ kind: "hello" });
    expect(frames[1]).toMatchObject({ kind: "end", status: "complete" });
  });
});
