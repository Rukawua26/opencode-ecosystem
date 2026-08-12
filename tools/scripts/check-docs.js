#!/usr/bin/env node
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");

let errors = 0;

function checkFile(relPath, checks) {
  const absPath = join(repoRoot, relPath);
  if (!existsSync(absPath)) {
    console.error(`[FAIL] ${relPath}: file not found`);
    errors++;
    return;
  }
  const content = readFileSync(absPath, "utf-8");
  for (const { name, pattern, shouldNotExist } of checks) {
    const found = pattern.test(content);
    if (shouldNotExist && found) {
      console.error(`[FAIL] ${relPath}: ${name}`);
      errors++;
    } else if (!shouldNotExist && !found) {
      console.error(`[FAIL] ${relPath}: ${name}`);
      errors++;
    }
  }
}

checkFile("README.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should not include local hypruse session history", pattern: /hypruse|ADR-004/i, shouldNotExist: true },
  { name: "should not claim an unmeasured 61 percent saving", pattern: /61%/, shouldNotExist: true },
  { name: "should not present deterministic checks as 137 agent checks", pattern: /137 checks locales/i, shouldNotExist: true },
  { name: "should document v1.9.0", pattern: /v1\.9\.0/, shouldNotExist: false },
  { name: "should mention local-model-router", pattern: /local-model-router/, shouldNotExist: false },
  { name: "should mention obsidian-ingest", pattern: /obsidian-ingest/, shouldNotExist: false },
  { name: "should document opt-in installer sync", pattern: /--sync/, shouldNotExist: false },
  { name: "should document read-only installer preview", pattern: /--dry-run/, shouldNotExist: false },
  { name: "should document structured doctor output", pattern: /opencode-doctor --json/, shouldNotExist: false },
  { name: "should document safe scaffolder names", pattern: /scaffolders[\s\S]*kebab-case/i, shouldNotExist: false },
  { name: "should distinguish deterministic checks from agent evals", pattern: /checks deterministas de software, no Agent Evals/i, shouldNotExist: false },
  { name: "should describe provider keys as optional", pattern: /API keys son opcionales/i, shouldNotExist: false },
]);

checkFile("README.es.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should document v1.9.0", pattern: /v1\.9\.0/, shouldNotExist: false },
  { name: "should mention local-model-router or Router local", pattern: /local-model-router|Router local/, shouldNotExist: false },
  { name: "should not duplicate obsolete plugin counts", pattern: /8 plugins|4 MCP servers/i, shouldNotExist: true },
]);

checkFile("docs/comparison.md", [
  { name: "should require Node.js 22 or newer", pattern: /Node\.js 22\+/, shouldNotExist: false },
  { name: "should not require obsolete Node.js 18", pattern: /Node\.js 18\+/, shouldNotExist: true },
  { name: "should not publish obsolete skills or plugin counts", pattern: /18 skills|18\+|Si \(8\)/i, shouldNotExist: true },
  { name: "should not publish unmeasured savings percentages", pattern: /\d{2,3}-\d{2,3}%/, shouldNotExist: true },
  { name: "should not claim unconfigured MCP servers", pattern: /playwright|5\+ MCP/i, shouldNotExist: true },
]);

checkFile("docs/_sidebar.md", [
  { name: "should not expose the historical v1.3 pending page", pattern: /pending-v1\.3|Pendientes v1\.3/i, shouldNotExist: true },
]);

checkFile("packages/memory-adapter/README.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should document v1.9.0", pattern: /v1\.9\.0/, shouldNotExist: false },
  { name: "should mention SQLite", pattern: /SQLite/, shouldNotExist: false },
  { name: "should mention MCP", pattern: /MCP/, shouldNotExist: false },
]);

checkFile("docs/architecture/diagrams.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should not include local hypruse session history", pattern: /hypruse|ADR-004/i, shouldNotExist: true },
]);

checkFile("docs/architecture/overview.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should not publish unmeasured savings percentages", pattern: /\d{2,3}-\d{2,3}%/, shouldNotExist: true },
]);

checkFile("docs/token-economy/study.md", [
  { name: "should mark savings as hypotheses", pattern: /Hipotesis/, shouldNotExist: false },
  { name: "should not publish unmeasured savings percentages", pattern: /\d{2,3}-\d{2,3}%/, shouldNotExist: true },
]);

checkFile("docs/README.md", [
  { name: "should not expose machine-local vault commands", pattern: /~\/docs\/scripts/, shouldNotExist: true },
]);

checkFile("assets/hero.svg", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
]);

checkFile("config/mcp/package.json", [
  { name: "should declare SDK", pattern: /@modelcontextprotocol\/sdk/, shouldNotExist: false },
]);

checkFile("config/plugins/sandbox.js", [
  { name: "should not use shell: true", pattern: /shell:\s*true/, shouldNotExist: true },
]);

checkFile("config/plugins/checkpoints.js", [
  { name: "should exclude .env", pattern: /\.env/, shouldNotExist: false },
]);

checkFile("tools/scripts/doctor.js", [
  { name: "should check router SDK", pattern: /@modelcontextprotocol\/sdk/, shouldNotExist: false },
]);

checkFile("install.sh", [
  { name: "should install v1.9.0 by default", pattern: /INSTALL_TAG=.*v1\.9\.0/, shouldNotExist: false },
]);

checkFile("install.ps1", [
  { name: "should install v1.9.0 by default", pattern: /InstallTag[\s\S]*v1\.9\.0/, shouldNotExist: false },
]);

if (errors === 0) {
  console.log("[OK] All documentation and contract checks passed");
  process.exit(0);
} else {
  console.error(`[FAIL] ${errors} check(s) failed`);
  process.exit(1);
}
