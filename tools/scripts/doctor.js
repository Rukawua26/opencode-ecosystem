#!/usr/bin/env node

import { existsSync, lstatSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";

const args = process.argv.slice(2);
const unknown = args.filter((arg) => arg !== "--json" && arg !== "--help" && arg !== "-h");
if (unknown.length > 0) {
  console.error(`Unknown option: ${unknown[0]}`);
  process.exit(2);
}
if (args.includes("--help") || args.includes("-h")) {
  console.log("Usage: opencode-doctor [--json]");
  process.exit(0);
}

const jsonMode = args.includes("--json");
const HOME = process.env.HOME || process.env.USERPROFILE || "/tmp";
const OPENCODE_DIR = join(HOME, ".config", "opencode");
const SKILLS_DIR = join(HOME, "opencode-custom", "skills");
const BIN_DIR = join(HOME, ".opencode", "bin");
const DATA_DIR = process.platform === "win32" && process.env.LOCALAPPDATA
  ? join(process.env.LOCALAPPDATA, "opencode", "plugins-data")
  : join(HOME, ".local", "share", "opencode", "plugins-data");
const MANIFEST_FILE = join(OPENCODE_DIR, ".ecosystem-managed-files");

const checks = [];

function addCheck(id, section, name, required, test) {
  let status;
  let detail;
  try {
    status = test() ? "pass" : required ? "fail" : "skip";
  } catch (error) {
    status = required ? "error" : "skip";
    if (required) detail = error.message;
  }
  checks.push({ id, section, name, status, required, ...(detail ? { detail } : {}) });
}

function commandWorks(command, commandArgs = ["--version"]) {
  return spawnSync(command, commandArgs, { stdio: "ignore", timeout: 5000, shell: process.platform === "win32" }).status === 0;
}

function parseEnv(filePath) {
  if (!existsSync(filePath)) return {};
  return Object.fromEntries(
    readFileSync(filePath, "utf8")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        return [line.slice(0, separator), line.slice(separator + 1).trim()];
      }),
  );
}

function managedDestination(logical) {
  if (logical.startsWith("opencode/")) return join(OPENCODE_DIR, logical.slice(9));
  if (logical.startsWith("skills/")) return join(SKILLS_DIR, logical.slice(7));
  if (logical.startsWith("bin/")) return join(BIN_DIR, logical.slice(4));
  return null;
}

function managedRoot(logical) {
  if (logical.startsWith("opencode/")) return OPENCODE_DIR;
  if (logical.startsWith("skills/")) return SKILLS_DIR;
  if (logical.startsWith("bin/")) return BIN_DIR;
  return null;
}

function isSafeManagedPath(logical) {
  if (!/^(opencode|skills|bin)\/.+/.test(logical)) return false;
  if (logical.includes("\\") || logical.includes(":") || logical.includes("//")) return false;
  return !logical.split("/").includes("..");
}

function isCanonicalManagedPath(logical) {
  return !logical.endsWith("/") && !logical.split("/").includes(".");
}

function isProtectedManagedPath(logical) {
  return logical === "opencode/opencode.jsonc" || logical === "opencode/.ecosystem-managed-files";
}

function tryLstat(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT" || error.code === "ENOTDIR") return null;
    throw error;
  }
}

function hasSymlinkComponent(destination, root) {
  const normalizedRoot = resolve(root);
  const normalizedDestination = resolve(destination);
  const rootStats = tryLstat(normalizedRoot);
  if (rootStats?.isSymbolicLink()) return true;
  const pathFromRoot = relative(normalizedRoot, normalizedDestination);
  if (!pathFromRoot || pathFromRoot === ".." || pathFromRoot.startsWith(`..${sep}`)) return true;
  let current = normalizedRoot;
  for (const segment of pathFromRoot.split(sep)) {
    current = join(current, segment);
    const stats = tryLstat(current);
    if (!stats) return false;
    if (stats.isSymbolicLink()) return true;
  }
  return false;
}

function inspectManifest() {
  const result = {
    status: "missing",
    path: "~/.config/opencode/.ecosystem-managed-files",
    entries: 0,
    present: 0,
    missing: [],
    issues: [],
    modified: { status: "unknown", reason: "manifest_has_no_content_hashes" },
  };
  if (!existsSync(MANIFEST_FILE)) {
    result.issues.push({ line: 0, code: "manifest_missing" });
    return result;
  }

  const lines = readFileSync(MANIFEST_FILE, "utf8").split(/\n/);
  if (lines.at(-1) === "") lines.pop();
  if (lines.length === 0) result.issues.push({ line: 0, code: "manifest_empty" });
  const seen = new Set();
  for (const [index, rawLine] of lines.entries()) {
    const line = index + 1;
    const entry = rawLine.endsWith("\r") ? rawLine.slice(0, -1) : rawLine;
    if (!entry) {
      result.issues.push({ line, code: "empty_entry" });
      continue;
    }
    result.entries++;
    if (entry !== entry.trim()) {
      result.issues.push({ line, code: "noncanonical_path", entry });
      continue;
    }
    if (seen.has(entry)) {
      result.issues.push({ line, code: "duplicate_entry", entry });
      continue;
    }
    seen.add(entry);
    if (!isCanonicalManagedPath(entry)) {
      result.issues.push({ line, code: "noncanonical_path", entry });
      continue;
    }
    if (!isSafeManagedPath(entry)) {
      result.issues.push({ line, code: "unsafe_path", entry });
      continue;
    }
    if (isProtectedManagedPath(entry)) {
      result.issues.push({ line, code: "protected_path", entry });
      continue;
    }
    const destination = managedDestination(entry);
    const root = managedRoot(entry);
    if (!destination || !root || hasSymlinkComponent(destination, root)) {
      result.issues.push({ line, code: "symlink_or_escape", entry });
      continue;
    }
    const destinationStats = tryLstat(destination);
    if (!destinationStats) {
      result.missing.push(entry);
      continue;
    }
    if (!destinationStats.isFile()) {
      result.issues.push({ line, code: "not_a_file", entry });
      continue;
    }
    result.present++;
  }
  result.missing.sort();
  result.issues.sort((a, b) => a.line - b.line || a.code.localeCompare(b.code));
  result.status = result.issues.length === 0 && result.missing.length === 0 ? "valid" : "invalid";
  return result;
}

addCheck("runtime.node", "runtime", "Node.js >= 22", true, () => Number(process.versions.node.split(".")[0]) >= 22);
addCheck("runtime.npm", "runtime", "npm available", true, () => commandWorks("npm"));
addCheck("runtime.git", "runtime", "git available", true, () => commandWorks("git"));
addCheck("opencode.config", "opencode", "opencode.jsonc", true, () => existsSync(join(OPENCODE_DIR, "opencode.jsonc")));
for (const directory of ["agents", "plugins", "mcp", "profiles"]) {
  addCheck(`opencode.${directory}`, "opencode", `${directory} directory`, true, () => {
    const path = join(OPENCODE_DIR, directory);
    return existsSync(path) && statSync(path).isDirectory();
  });
}
addCheck("opencode.skills", "opencode", "skills directory", true, () => existsSync(SKILLS_DIR) && statSync(SKILLS_DIR).isDirectory());
addCheck("opencode.plugins-data", "opencode", "plugins-data directory", true, () => existsSync(DATA_DIR) && statSync(DATA_DIR).isDirectory());

const memoryDir = join(OPENCODE_DIR, "mcp", "memory-adapter");
for (const [id, file] of [
  ["package", "package.json"],
  ["adapter", join("src", "adapter.js")],
  ["server", join("src", "mcp-server.js")],
  ["cli", join("src", "cli.js")],
]) {
  addCheck(`memory.${id}`, "memory", `memory-adapter/${file}`, true, () => existsSync(join(memoryDir, file)));
}

const mcpDir = join(OPENCODE_DIR, "mcp");
addCheck("router.package", "router", "router package.json", true, () => existsSync(join(mcpDir, "package.json")));
addCheck("router.source", "router", "router local-model-router.js", true, () => existsSync(join(mcpDir, "local-model-router.js")));
addCheck("router.sdk", "router", "router @modelcontextprotocol/sdk installed", true, () => existsSync(join(mcpDir, "node_modules", "@modelcontextprotocol", "sdk", "package.json")));

const manifest = inspectManifest();
addCheck("manifest.integrity", "manifest", "managed manifest valid", true, () => manifest.status === "valid");

addCheck("optional.ollama", "optional", "Ollama server", false, () => commandWorks("ollama", ["list"]));
addCheck("optional.doctor-command", "optional", "opencode-doctor installed", false, () => {
  const suffix = process.platform === "win32" ? ".cmd" : "";
  return existsSync(join(BIN_DIR, `opencode-doctor${suffix}`));
});
const environment = parseEnv(join(OPENCODE_DIR, ".env"));
const providers = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"];
addCheck("optional.provider", "providers", "at least one provider key configured", false, () => providers.some((key) => Boolean(environment[key] || process.env[key])));

const requiredChecks = checks.filter((check) => check.required);
const summary = {
  passed: checks.filter((check) => check.status === "pass").length,
  failed: checks.filter((check) => check.status === "fail").length,
  errors: checks.filter((check) => check.status === "error").length,
  skipped: checks.filter((check) => check.status === "skip").length,
  required: requiredChecks.length,
};
const ok = requiredChecks.every((check) => check.status === "pass");

if (jsonMode) {
  console.log(JSON.stringify({ schemaVersion: 1, ok, checks, summary, manifest }, null, 2));
} else {
  const sections = [
    ["runtime", "Runtime"],
    ["opencode", "OpenCode"],
    ["memory", "Memory adapter"],
    ["router", "Local model router"],
    ["manifest", "Managed manifest"],
    ["optional", "Optional services"],
    ["providers", "Providers"],
  ];
  console.log("\n=== OpenCode Ecosystem Doctor ===");
  for (const [id, label] of sections) {
    console.log(`\n--- ${label} ---`);
    for (const check of checks.filter((item) => item.section === id)) {
      const prefix = check.status === "pass" ? "OK" : check.status === "skip" ? "SKIP" : check.status.toUpperCase();
      console.log(`[${prefix}] ${check.name}${check.detail ? `: ${check.detail}` : ""}`);
    }
  }
  console.log("\n=== Summary ===");
  console.log(`Checks: ${requiredChecks.filter((check) => check.status === "pass").length}/${requiredChecks.length} passed`);
}

process.exitCode = ok ? 0 : 1;
