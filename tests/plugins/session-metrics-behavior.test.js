import { afterEach, describe, expect, it, vi } from "vitest";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import sessionMetricsPlugin from "../../config/plugins/session-metrics.js";

const tempDirs = [];

afterEach(() => {
  vi.resetModules();
  delete process.env.OPENCODE_METRICS_FILE;
  delete process.env.OPENCODE_EFFORT_MODE;
  for (const dir of tempDirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

async function loadPlugin() {
  const dir = mkdtempSync(join(tmpdir(), "opencode-metrics-test-"));
  tempDirs.push(dir);
  const file = join(dir, "metrics.jsonl");
  process.env.OPENCODE_METRICS_FILE = file;
  return { hooks: await sessionMetricsPlugin(), file };
}

function assistantInfo(sessionID, id, completed = 200) {
  return {
    id,
    sessionID,
    role: "assistant",
    providerID: "test",
    modelID: "model",
    time: { created: 100, completed },
    tokens: { input: 1, output: 1 },
  };
}

describe("Session metrics behavior", () => {
  it("records deltas, broad reads, effort and verification", async () => {
    const { hooks, file } = await loadPlugin();
    const sessionID = "metrics-session";
    await hooks["tool.execute.before"]({ sessionID, tool: "read", args: { path: "**/*" } });
    await hooks["tool.execute.before"]({ sessionID, tool: "task", args: {} });
    await hooks.event({ event: { type: "message.updated", properties: {
      sessionID,
      info: { id: "assistant-pending", sessionID, role: "assistant", time: { created: 90 } },
    } } });
    await hooks.event({ event: { type: "message.updated", properties: {
      sessionID,
      info: { id: "user-1", sessionID, role: "user", text: "/effort max /verify" },
    } } });
    await hooks.event({ event: { type: "message.updated", properties: {
      sessionID,
      info: assistantInfo(sessionID, "assistant-1"),
    } } });

    expect(existsSync(file)).toBe(true);
    const first = JSON.parse(readFileSync(file, "utf8").trim());
    expect(first.tools).toBe(2);
    expect(first.delegations).toBe(1);
    expect(first.reads_broad).toBe(1);
    expect(first.effort_mode).toBe("max");
    expect(first.verified).toBe(true);

    await hooks.event({ event: { type: "message.updated", properties: {
      sessionID,
      info: assistantInfo(sessionID, "assistant-2", 300),
    } } });
    const records = readFileSync(file, "utf8").trim().split("\n").map(JSON.parse);
    expect(records[1].tools).toBe(0);
    expect(records[1].delegations).toBe(0);
    expect(records[1].reads_broad).toBe(0);
  });

  it("marks repeated tools as a loop for one metric", async () => {
    const { hooks, file } = await loadPlugin();
    const sessionID = "metrics-loop";
    for (let index = 0; index < 10; index++) {
      await hooks["tool.execute.before"]({ sessionID, tool: "read", args: { path: "file.js" } });
    }
    await hooks.event({ event: { type: "message.updated", properties: {
      sessionID,
      info: assistantInfo(sessionID, "loop-1"),
    } } });
    await hooks.event({ event: { type: "message.updated", properties: {
      sessionID,
      info: assistantInfo(sessionID, "loop-2", 300),
    } } });
    const records = readFileSync(file, "utf8").trim().split("\n").map(JSON.parse);
    expect(records[0].loop_detected).toBe(true);
    expect(records[1].loop_detected).toBe(false);
  });
});
