import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, rmSync, writeFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const SCRIPTS = [
  "tools/scripts/doctor.js",
  "tools/scripts/profile.js",
  "tools/scripts/skills.js",
  "tools/scripts/opencode-metrics.js",
];

let home;

function createTempHome() {
  home = mkdtempSync(join(tmpdir(), "opencode-import-safety-"));
  writeFileSync(join(home, ".env"), "");
}

function cleanup() {
  rmSync(home, { recursive: true, force: true });
}

function runAsImport(scriptPath) {
  return spawnSync(process.execPath, ["-e", `import("${scriptPath}")`], {
    encoding: "utf8",
    env: { ...process.env, HOME: home, USERPROFILE: home, LOCALAPPDATA: home, NODE_DISABLE_COMPILE_CACHE: "1" },
    timeout: 10000,
  });
}

function runDirect(scriptPath, args = []) {
  const fullPath = join(repoRoot, scriptPath);
  return spawnSync(process.execPath, [fullPath, ...args], {
    encoding: "utf8",
    env: { ...process.env, HOME: home, USERPROFILE: home, LOCALAPPDATA: home, NODE_DISABLE_COMPILE_CACHE: "1" },
    timeout: 10000,
  });
}

beforeEach(createTempHome);
afterEach(cleanup);

describe("Tool Scripts Import Safety", () => {
  it.each(SCRIPTS)(
    "importing %s does not produce stdout, stderr, or exit with non-zero",
    (scriptPath) => {
      const fullPath = join(repoRoot, scriptPath);
      const result = runAsImport(fullPath);
      expect(result.status).toBe(0);
      expect(result.stdout).toBe("");
      expect(result.stderr).toBe("");
    },
  );

  it.each(SCRIPTS)(
    "importing %s does not create files in HOME",
    (scriptPath) => {
      const fullPath = join(repoRoot, scriptPath);
      const before = readdirSync(home);
      runAsImport(fullPath);
      const after = readdirSync(home);
      expect(after.sort()).toEqual(before.sort());
    },
  );

  it.each(SCRIPTS)(
    "direct invocation of %s executes main() without crashing",
    (scriptPath) => {
      const fullPath = join(repoRoot, scriptPath);
      const args = scriptPath === "tools/scripts/doctor.js" ? ["--help"]
        : scriptPath === "tools/scripts/opencode-metrics.js" ? ["1"]
        : [];
      const result = runDirect(fullPath, args);
      expect(result.status).not.toBeNull();
      const hasOutput = result.stdout.length > 0 || result.stderr.length > 0;
      expect(hasOutput).toBe(true);
    },
  );
});
