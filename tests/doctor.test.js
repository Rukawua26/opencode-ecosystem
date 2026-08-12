import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, readlinkSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const doctor = join(repoRoot, "tools", "scripts", "doctor.js");
const doctorWrapper = join(repoRoot, "tools", "scripts", "opencode-doctor.sh");
let home;

function write(relativePath, content = "fixture") {
  const path = join(home, relativePath);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content);
}

function createValidInstall() {
  for (const directory of [
    ".config/opencode/agents",
    ".config/opencode/plugins",
    ".config/opencode/mcp/profiles-placeholder",
    ".config/opencode/profiles",
    ".local/share/opencode/plugins-data",
    "opencode-custom/skills",
  ]) mkdirSync(join(home, directory), { recursive: true });
  for (const file of [
    ".config/opencode/opencode.jsonc",
    ".config/opencode/mcp/memory-adapter/package.json",
    ".config/opencode/mcp/memory-adapter/src/adapter.js",
    ".config/opencode/mcp/memory-adapter/src/mcp-server.js",
    ".config/opencode/mcp/memory-adapter/src/cli.js",
    ".config/opencode/mcp/package.json",
    ".config/opencode/mcp/local-model-router.js",
    ".config/opencode/mcp/node_modules/@modelcontextprotocol/sdk/package.json",
    ".config/opencode/plugins/guardrails.js",
  ]) write(file);
  write(".config/opencode/.ecosystem-managed-files", "opencode/plugins/guardrails.js\n");
}

function runDoctor(args = []) {
  return spawnSync(process.execPath, [doctor, ...args], {
    encoding: "utf8",
    env: { ...process.env, HOME: home, USERPROFILE: home, LOCALAPPDATA: home, NODE_DISABLE_COMPILE_CACHE: "1", OPENAI_API_KEY: "", ANTHROPIC_API_KEY: "", GOOGLE_API_KEY: "", GEMINI_API_KEY: "" },
  });
}

function snapshot(root, current = root) {
  return readdirSync(current, { withFileTypes: true })
    .flatMap((entry) => {
      const path = join(current, entry.name);
      const relativePath = path.slice(root.length + 1);
      const stats = lstatSync(path);
      if (stats.isSymbolicLink()) return [`${relativePath}|link|${readlinkSync(path)}`];
      if (stats.isDirectory()) return [`${relativePath}|dir`, ...snapshot(root, path)];
      return [`${relativePath}|file|${readFileSync(path, "base64")}`];
    })
    .sort();
}

beforeEach(() => {
  home = mkdtempSync(join(tmpdir(), "opencode-doctor-"));
  createValidInstall();
});

afterEach(() => rmSync(home, { recursive: true, force: true }));

describe("opencode-doctor", () => {
  it("emits one stable JSON document for a valid installation", () => {
    const before = snapshot(home);
    const result = runDoctor(["--json"]);
    if (result.status !== 0) console.error("DEBUG stderr:", result.stderr, "DEBUG stdout:", result.stdout);
    expect(result.status).toBe(0);
    expect(result.stderr).toBe("");
    const report = JSON.parse(result.stdout);
    expect(report.schemaVersion).toBe(1);
    expect(report.ok).toBe(true);
    expect(report.manifest).toMatchObject({ status: "valid", entries: 1, present: 1, missing: [] });
    expect(report.manifest.modified).toEqual({ status: "unknown", reason: "manifest_has_no_content_hashes" });
    expect(report.checks.map((check) => check.id)).toContain("manifest.integrity");
    expect(snapshot(home)).toEqual(before);
  });

  it("reports missing managed files without inventing modification status", () => {
    rmSync(join(home, ".config/opencode/plugins/guardrails.js"));
    const result = runDoctor(["--json"]);
    expect(result.status).toBe(1);
    const report = JSON.parse(result.stdout);
    expect(report.ok).toBe(false);
    expect(report.manifest.status).toBe("invalid");
    expect(report.manifest.missing).toEqual(["opencode/plugins/guardrails.js"]);
    expect(report.manifest.modified.status).toBe("unknown");
  });

  it("rejects unsafe, protected, duplicate, empty, and symlink entries deterministically", () => {
    const victim = join(home, "victim.js");
    writeFileSync(victim, "unchanged");
    symlinkSync(victim, join(home, ".config/opencode/plugins/link.js"));
    write(".config/opencode/.ecosystem-managed-files", [
      "opencode/plugins/guardrails.js",
      "opencode/plugins/guardrails.js",
      "opencode/../../escape",
      "opencode/opencode.jsonc",
      "opencode/plugins/link.js",
      "",
      " opencode/plugins/spaced.js",
      "opencode/./plugins/guardrails.js",
    ].join("\n"));
    const result = runDoctor(["--json"]);
    const report = JSON.parse(result.stdout);
    expect(result.status).toBe(1);
    expect(report.manifest.issues.map((issue) => issue.code)).toEqual([
      "duplicate_entry",
      "unsafe_path",
      "protected_path",
      "symlink_or_escape",
      "empty_entry",
      "noncanonical_path",
      "noncanonical_path",
    ]);
    expect(readFileSync(victim, "utf8")).toBe("unchanged");
  });

  it("reports a dangling managed symlink as unsafe rather than missing", () => {
    symlinkSync(join(home, "missing-target.js"), join(home, ".config/opencode/plugins/dangling.js"));
    write(".config/opencode/.ecosystem-managed-files", "opencode/plugins/dangling.js\n");
    const result = runDoctor(["--json"]);
    const report = JSON.parse(result.stdout);
    expect(result.status).toBe(1);
    expect(report.manifest.missing).toEqual([]);
    expect(report.manifest.issues).toEqual([
      { line: 1, code: "symlink_or_escape", entry: "opencode/plugins/dangling.js" },
    ]);
  });

  it("rejects an empty manifest", () => {
    write(".config/opencode/.ecosystem-managed-files", "");
    const result = runDoctor(["--json"]);
    const report = JSON.parse(result.stdout);
    expect(result.status).toBe(1);
    expect(report.manifest.status).toBe("invalid");
    expect(report.manifest.issues).toEqual([{ line: 0, code: "manifest_empty" }]);
  });

  it("reports a missing manifest", () => {
    rmSync(join(home, ".config/opencode/.ecosystem-managed-files"));
    const result = runDoctor(["--json"]);
    const report = JSON.parse(result.stdout);
    expect(result.status).toBe(1);
    expect(report.manifest.status).toBe("missing");
    expect(report.manifest.issues).toEqual([{ line: 0, code: "manifest_missing" }]);
  });

  it("preserves human output and required-check exit semantics", () => {
    const result = runDoctor();
    expect(result.status).toBe(0);
    expect(result.stdout).toContain("=== OpenCode Ecosystem Doctor ===");
    expect(result.stdout).toContain("--- Managed manifest ---");
    expect(result.stdout).toContain("Checks: 18/18 passed");
    expect(() => JSON.parse(result.stdout)).toThrow();
  });

  it("uses exit code 2 for unknown options", () => {
    const result = runDoctor(["--unknown"]);
    expect(result.status).toBe(2);
    expect(result.stderr).toContain("Unknown option");
  });

  it("keeps HOME and TMP read-only through the public wrapper", () => {
    const temp = mkdtempSync(join(tmpdir(), "opencode-doctor-tmp-"));
    write(".config/opencode/tools/doctor.js", readFileSync(doctor, "utf8"));
    const before = snapshot(home);
    const result = spawnSync("bash", [doctorWrapper, "--json"], {
      encoding: "utf8",
      env: { ...process.env, HOME: home, USERPROFILE: home, LOCALAPPDATA: home, TMPDIR: temp },
    });
    expect(result.status).toBe(0);
    expect(JSON.parse(result.stdout).ok).toBe(true);
    expect(snapshot(home)).toEqual(before);
    expect(readdirSync(temp)).toEqual([]);
    rmSync(temp, { recursive: true, force: true });
  });
});
