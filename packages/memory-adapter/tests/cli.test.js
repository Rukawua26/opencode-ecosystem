import { afterEach, beforeEach, describe, it } from "node:test";
import { strict as assert } from "node:assert";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  symlinkSync,
  truncateSync,
  writeFileSync,
} from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { parseEventJsonl } from "../src/memory-events.js";

const CLI = fileURLToPath(new URL("../src/cli.js", import.meta.url));
const ROOT = join(tmpdir(), "memory-adapter-cli-incremental");
const PROJECT_PATH = join(ROOT, "project");
const DB = join(ROOT, "memory.db");

describe("memory-adapter incremental event CLI", () => {
  beforeEach(() => {
    rmSync(ROOT, { recursive: true, force: true });
    mkdirSync(PROJECT_PATH, { recursive: true });
  });

  afterEach(() => rmSync(ROOT, { recursive: true, force: true }));

  function run(...args) {
    return spawnSync(process.execPath, [CLI, ...args, "--db", DB, "--project", "incremental-cli", "--path", PROJECT_PATH], {
      encoding: "utf8",
      env: { ...process.env, HOME: ROOT },
    });
  }

  function save(title, extra = []) {
    const result = run("save-decision", "--title", title, "--content", title, ...extra);
    assert.strictEqual(result.status, 0, result.stderr);
  }

  function exportDelta(state, out, limit = 1) {
    return run("export-events", "--kind", "decision", "--limit", String(limit), "--state", state, "--out", out);
  }

  it("exports only new public events across repeated limited runs", () => {
    const state = join(ROOT, "state.jsonl");
    const out = join(ROOT, "delta.jsonl");
    save("Oldest");
    save("Private", ["--private"]);

    let result = exportDelta(state, out);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.deepStrictEqual(parseEventJsonl(readFileSync(out, "utf8")).map((event) => event.content.title), ["Oldest"]);
    assert.strictEqual(parseEventJsonl(readFileSync(state, "utf8")).length, 1);

    save("Middle");
    save("Newest");
    result = exportDelta(state, out);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.deepStrictEqual(parseEventJsonl(readFileSync(out, "utf8")).map((event) => event.content.title), ["Newest"]);

    result = exportDelta(state, out);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.deepStrictEqual(parseEventJsonl(readFileSync(out, "utf8")).map((event) => event.content.title), ["Middle"]);

    result = exportDelta(state, out);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.strictEqual(readFileSync(out, "utf8"), "");
    assert.strictEqual(parseEventJsonl(readFileSync(state, "utf8")).length, 3);
  });

  it("does not modify output or state when the state hash is invalid", () => {
    const state = join(ROOT, "state.jsonl");
    const out = join(ROOT, "delta.jsonl");
    save("Valid");
    assert.strictEqual(exportDelta(state, out).status, 0);

    const tampered = readFileSync(state, "utf8").replace("Valid", "Tampered");
    writeFileSync(state, tampered);
    writeFileSync(out, "unchanged");
    const result = exportDelta(state, out);

    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /hash mismatch/);
    assert.strictEqual(readFileSync(state, "utf8"), tampered);
    assert.strictEqual(readFileSync(out, "utf8"), "unchanged");
  });

  it("replaces a known event version when the same row changes", () => {
    const state = join(ROOT, "state.jsonl");
    const out = join(ROOT, "delta.jsonl");
    let result = run("save-preference", "--key", "theme", "--value", "light");
    assert.strictEqual(result.status, 0, result.stderr);

    result = run("export-events", "--kind", "preference", "--state", state, "--out", out);
    assert.strictEqual(result.status, 0, result.stderr);
    const previous = parseEventJsonl(readFileSync(state, "utf8"))[0];

    result = run("save-preference", "--key", "theme", "--value", "dark");
    assert.strictEqual(result.status, 0, result.stderr);
    result = run("export-events", "--kind", "preference", "--state", state, "--out", out);

    assert.strictEqual(result.status, 0, result.stderr);
    const delta = parseEventJsonl(readFileSync(out, "utf8"));
    const merged = parseEventJsonl(readFileSync(state, "utf8"));
    assert.strictEqual(delta[0].event_id, previous.event_id);
    assert.strictEqual(delta[0].content.value, "dark");
    assert.notStrictEqual(delta[0].content_hash, previous.content_hash);
    assert.deepStrictEqual(merged, delta);
  });

  it("rejects using the same path for state and delta output", () => {
    const target = join(ROOT, "events.jsonl");
    save("One");
    const result = exportDelta(target, target);

    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /different files/);
    assert.strictEqual(existsSync(target), false);
  });

  it("rejects output aliases and active state locks", () => {
    const state = join(ROOT, "state.jsonl");
    const alias = join(ROOT, "state-alias.jsonl");
    const out = join(ROOT, "delta.jsonl");
    writeFileSync(state, "");
    symlinkSync(state, alias);

    let result = exportDelta(state, alias);
    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /aliases of the same file/);
    assert.strictEqual(readFileSync(state, "utf8"), "");

    writeFileSync(`${state}.lock`, JSON.stringify({ pid: process.pid, created_at: new Date().toISOString() }));
    result = exportDelta(state, out);
    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /state is locked/);
    assert.strictEqual(existsSync(out), false);
  });

  it("recovers a state lock owned by a dead process", () => {
    const state = join(ROOT, "state.jsonl");
    const out = join(ROOT, "delta.jsonl");
    save("One");
    writeFileSync(`${state}.lock`, JSON.stringify({ pid: 2147483647, created_at: "2000-01-01T00:00:00.000Z" }));

    const result = exportDelta(state, out);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.strictEqual(parseEventJsonl(readFileSync(out, "utf8")).length, 1);
    assert.strictEqual(existsSync(`${state}.lock`), false);
  });

  it("rejects oversized state files before reading or writing output", () => {
    const state = join(ROOT, "oversized-state.jsonl");
    const out = join(ROOT, "delta.jsonl");
    writeFileSync(state, "");
    truncateSync(state, 64 * 1024 * 1024 + 1);
    writeFileSync(out, "unchanged");

    const result = exportDelta(state, out);
    assert.notStrictEqual(result.status, 0);
    assert.match(result.stderr, /exceeds 64 MiB/);
    assert.strictEqual(readFileSync(out, "utf8"), "unchanged");
  });
});
