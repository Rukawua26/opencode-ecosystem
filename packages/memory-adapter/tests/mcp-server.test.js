import { after, before, describe, it } from "node:test";
import { strict as assert } from "node:assert";
import { mkdirSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawn } from "node:child_process";
import { MemoryAdapter } from "../src/adapter.js";
import { fileURLToPath } from "node:url";

const HOME = join(tmpdir(), "test-memory-mcp");
const PROJECT_ROOT = join(HOME, "trusted-project");
const PROJECT_NAME = "trusted-project-test";
const DB_PATH = join(HOME, ".local", "share", "opencode", "memory-adapter", "memory.db");
const SERVER = fileURLToPath(new URL("../src/mcp-server.js", import.meta.url));

describe("memory MCP server", () => {
  let child;
  let buffer = "";
  const pending = [];

  function request(method, params) {
    const id = pending.length + 1;
    return new Promise((resolve, reject) => {
      pending.push({ id, resolve, reject });
      child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
    });
  }

  before(async () => {
    if (existsSync(HOME)) rmSync(HOME, { recursive: true, force: true });
    mkdirSync(PROJECT_ROOT, { recursive: true });
    const setup = new MemoryAdapter(DB_PATH).init();
    setup.saveDecision({
      project: PROJECT_NAME,
      projectPath: PROJECT_ROOT,
      title: "Trusted decision",
      content: "Visible only in the trusted project",
      tags: "feature:001,receipt:r1",
    });
    setup.saveDecision({
      project: PROJECT_NAME,
      projectPath: PROJECT_ROOT,
      title: "Private trusted decision",
      content: "Must never leave the local CLI",
      isPrivate: true,
    });
    setup.savePreference({
      project: PROJECT_NAME,
      projectPath: PROJECT_ROOT,
      key: "api_key",
      value: "must-require-explicit-kind",
    });
    setup.saveSessionAction({
      project: PROJECT_NAME,
      projectPath: PROJECT_ROOT,
      action: "touched_secret",
      filesTouched: ".env",
    });
    setup.saveDecision({
      project: "other-project",
      projectPath: join(HOME, "other-project"),
      title: "Other decision",
      content: "Must not cross project boundaries",
    });
    setup.close();
    child = spawn(process.execPath, [SERVER], {
      cwd: PROJECT_ROOT,
      env: {
        ...process.env,
        HOME,
        PATH: process.env.PATH,
        OPENCODE_PROJECT_ROOT: PROJECT_ROOT,
        OPENCODE_PROJECT_NAME: PROJECT_NAME,
      },
      stdio: ["pipe", "pipe", "pipe"],
      detached: true,
    });
    child.stdout.on("data", (chunk) => {
      buffer += chunk.toString();
      let newline;
      while ((newline = buffer.indexOf("\n")) >= 0) {
        const message = JSON.parse(buffer.slice(0, newline));
        buffer = buffer.slice(newline + 1);
        const index = pending.findIndex((item) => item.id === message.id);
        if (index >= 0) pending.splice(index, 1)[0].resolve(message);
      }
    });
    await new Promise((r) => setTimeout(r, 500));
  });

  after(async () => {
    if (child && !child.killed) {
      child.stdin.end();
      child.kill("SIGTERM");
      await new Promise((resolve) => {
        const timeout = setTimeout(resolve, 1000);
        child.on("exit", () => {
          clearTimeout(timeout);
          resolve();
        });
      });
    }
    if (existsSync(HOME)) rmSync(HOME, { recursive: true, force: true });
  });

  it("exposes only read-only tools without private export", async () => {
    const initialized = await request("initialize", {});
    const response = await request("tools/list", {});
    const names = response.result.tools.map((item) => item.name);
    const exportTool = response.result.tools.find((item) => item.name === "export_project");

    assert.ok(!names.includes("import_project"));
    assert.ok(!names.includes("export_to_obsidian"));
    assert.ok(!names.some((name) => name.startsWith("save_")));
    assert.ok(names.includes("list_events"));
    assert.ok(names.includes("export_events"));
    assert.ok(!Object.hasOwn(exportTool.inputSchema.properties, "includePrivate"));
    assert.ok(!Object.hasOwn(exportTool.inputSchema.properties, "project"));
    assert.strictEqual(initialized.result.serverInfo.version, "1.8.0");
  });

  it("rejects unknown arguments and invalid types", async () => {
    const response = await request("tools/call", {
      name: "search_memory",
      arguments: {
        query: "decision",
        limit: "unbounded",
      },
    });

    assert.strictEqual(response.result.isError, true);
    assert.match(response.result.content[0].text, /limit must be a number/);

    const zeroLimit = await request("tools/call", {
      name: "list_events",
      arguments: { limit: 0 },
    });
    assert.strictEqual(zeroLimit.result.isError, true);
    assert.match(zeroLimit.result.content[0].text, /positive integer/);
  });

  it("binds reads to the trusted project without creating metadata", async () => {
    const context = await request("tools/call", { name: "get_context", arguments: {} });
    const payload = JSON.parse(context.result.content[0].text);
    assert.deepStrictEqual(payload.recentDecisions.map((item) => item.title), ["Trusted decision"]);

    const database = new MemoryAdapter(DB_PATH).init();
    const projects = database.db.prepare("SELECT name FROM projects ORDER BY name").all();
    database.close();
    assert.deepStrictEqual(projects.map((item) => item.name), ["other-project", PROJECT_NAME]);
  });

  it("lists and exports only canonical non-private events", async () => {
    const listed = await request("tools/call", {
      name: "list_events",
      arguments: { kind: "decision", limit: 10 },
    });
    const events = JSON.parse(listed.result.content[0].text);
    assert.deepStrictEqual(events.map((event) => event.content.title), ["Trusted decision"]);
    assert.deepStrictEqual(events[0].tags, [["feature", "001"], ["receipt", "r1"]]);

    const exported = await request("tools/call", {
      name: "export_events",
      arguments: { kind: "decision", limit: 10 },
    });
    const lines = exported.result.content[0].text.trim().split("\n");
    assert.strictEqual(lines.length, 1);
    assert.strictEqual(JSON.parse(lines[0]).content.title, "Trusted decision");

    const safeDefault = await request("tools/call", {
      name: "export_events",
      arguments: { limit: 10 },
    });
    const defaultKinds = safeDefault.result.content[0].text.trim().split("\n")
      .filter(Boolean).map((line) => JSON.parse(line).kind);
    assert.ok(!defaultKinds.includes("preference"));
    assert.ok(!defaultKinds.includes("operational"));

    const explicitOperational = await request("tools/call", {
      name: "list_events",
      arguments: { kind: "operational", limit: 10 },
    });
    assert.deepStrictEqual(
      JSON.parse(explicitOperational.result.content[0].text).map((event) => event.kind),
      ["operational"],
    );
  });
});
