import { describe, it } from "node:test";
import { strict as assert } from "node:assert";
import {
  parseEventJsonl,
  toMemoryEvent,
  validateMemoryEvent,
} from "../src/memory-events.js";

describe("memory event projection", () => {
  const decision = {
    id: 7,
    category: "architecture",
    title: "Use local event projections",
    content: "Project existing rows instead of duplicating them.",
    rationale: "YAGNI",
    tags: "feature:001,receipt:r1,lens:verifier,file:src/adapter.js",
    created_at: "2026-08-10 12:00:00",
  };

  it("creates deterministic canonical events", () => {
    const first = toMemoryEvent(decision, "decision", "opencode-ecosystem");
    const second = toMemoryEvent({ ...decision }, "decision", "opencode-ecosystem");

    assert.deepStrictEqual(second, first);
    assert.match(first.content_hash, /^[a-f0-9]{64}$/);
    assert.strictEqual(first.event_id, "decision:opencode-ecosystem:7");
  });

  it("preserves optional RDD references as canonical tags", () => {
    const event = toMemoryEvent(decision, "decision", "opencode-ecosystem", {
      commit: "abc123",
      test: ["node:test", "lint"],
    });

    assert.deepStrictEqual(event.tags, [
      ["feature", "001"],
      ["receipt", "r1"],
      ["lens", "verifier"],
      ["file", "src/adapter.js"],
      ["commit", "abc123"],
      ["test", "node:test"],
      ["test", "lint"],
    ]);
  });

  it("rejects modified JSONL events", () => {
    const event = toMemoryEvent(decision, "decision", "opencode-ecosystem");
    const jsonl = `${JSON.stringify(event)}\n`;

    assert.deepStrictEqual(parseEventJsonl(jsonl), [event]);

    const modified = { ...event, content: { ...event.content, title: "Tampered" } };
    assert.throws(() => validateMemoryEvent(modified), /hash mismatch/);
    assert.throws(() => parseEventJsonl(`${JSON.stringify(modified)}\n`), /line 1/);
  });
});
