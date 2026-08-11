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
  { name: "should mention local-model-router", pattern: /local-model-router/, shouldNotExist: false },
  { name: "should mention obsidian-ingest", pattern: /obsidian-ingest/, shouldNotExist: false },
]);

checkFile("README.es.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should mention local-model-router or Router local", pattern: /local-model-router|Router local/, shouldNotExist: false },
]);

checkFile("packages/memory-adapter/README.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
  { name: "should mention SQLite", pattern: /SQLite/, shouldNotExist: false },
  { name: "should mention MCP", pattern: /MCP/, shouldNotExist: false },
]);

checkFile("docs/architecture/diagrams.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
]);

checkFile("docs/architecture/overview.md", [
  { name: "should not claim FTS5", pattern: /FTS5/i, shouldNotExist: true },
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

if (errors === 0) {
  console.log("[OK] All documentation and contract checks passed");
  process.exit(0);
} else {
  console.error(`[FAIL] ${errors} check(s) failed`);
  process.exit(1);
}
