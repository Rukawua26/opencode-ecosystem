#!/usr/bin/env node

import { readFileSync, existsSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execSync, spawn } from "node:child_process";
import { exit } from "node:process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const HOME = process.env.HOME || process.env.USERPROFILE;
const OPENCODE_DIR = join(HOME, ".config", "opencode");
const DATA_DIR = join(HOME, ".local", "share", "opencode", "plugins-data");

let checks = 0;
let passed = 0;

function check(name, fn) {
  checks++;
  try {
    if (fn()) {
      passed++;
      console.log(`[OK] ${name}`);
      return true;
    } else {
      console.log(`[FAIL] ${name}`);
      return false;
    }
  } catch (err) {
    console.log(`[ERROR] ${name}: ${err.message}`);
    return false;
  }
}

function checkFile(path, desc) {
  return check(desc, () => existsSync(path));
}

function checkDir(path, desc) {
  return check(desc, () => existsSync(path) && statSync(path).isDirectory());
}

function checkCmd(cmd, desc) {
  return check(desc, () => {
    try {
      execSync(`which ${cmd} 2>/dev/null || command -v ${cmd}`, { stdio: "pipe" });
      return true;
    } catch {
      return false;
    }
  });
}

console.log("\n=== OpenCode Ecosystem Doctor ===\n");

console.log("--- Sistema y Dependencias ---");
checkCmd("node", "Node.js disponible");
checkCmd("npm", "npm disponible");
checkCmd("git", "git disponible");

console.log("\n--- OpenCode Config ---");
checkFile(join(OPENCODE_DIR, "opencode.jsonc"), "opencode.jsonc");
checkDir(join(OPENCODE_DIR, "agents"), "agents directory");
checkDir(join(OPENCODE_DIR, "plugins"), "plugins directory");
checkDir(join(OPENCODE_DIR, "mcp"), "mcp directory");
checkDir(join(OPENCODE_DIR, "profiles"), "profiles directory");

console.log("\n--- Skills ---");
checkDir(join(HOME, "opencode-custom", "skills"), "skills directory");

console.log("\n--- Data Directory ---");
checkDir(DATA_DIR, "plugins-data directory");

console.log("\n--- Memory Adapter ---");
const memAdapterDir = join(OPENCODE_DIR, "mcp", "memory-adapter");
if (existsSync(memAdapterDir)) {
  checkFile(join(memAdapterDir, "package.json"), "memory-adapter package.json");
  checkFile(join(memAdapterDir, "src", "adapter.js"), "memory-adapter adapter.js");
  checkFile(join(memAdapterDir, "src", "mcp-server.js"), "memory-adapter mcp-server.js");

  check("memory-adapter dependencies", () => {
    try {
      execSync("npm ls --depth=0", { cwd: memAdapterDir, stdio: "pipe" });
      return true;
    } catch {
      return false;
    }
  });
} else {
  console.log("[SKIP] memory-adapter directory not found");
}

console.log("\n--- Ollama Local Models ---");
check("Ollama server", () => {
  try {
    execSync("ollama list", { stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
});

console.log("\n--- API Keys ---");
const envFile = join(OPENCODE_DIR, ".env");
if (existsSync(envFile)) {
  const content = readFileSync(envFile, "utf-8");
  const hasOpenAI = content.includes("OPENAI_API_KEY");
  const hasAnthropic = content.includes("ANTHROPIC_API_KEY");
  const hasGoogle = content.includes("GOOGLE_API_KEY");

  check("OPENAI_API_KEY set", () => hasOpenAI && !content.includes("OPENAI_API_KEY="));
  check("ANTHROPIC_API_KEY set", () => hasAnthropic && !content.includes("ANTHROPIC_API_KEY="));
  check("GOOGLE_API_KEY set", () => hasGoogle && !content.includes("GOOGLE_API_KEY="));
} else {
  console.log("[SKIP] .env file not found (run install.sh first)");
}

console.log("\n=== Summary ===");
console.log(`Checks: ${passed}/${checks} passed`);

if (passed === checks) {
  console.log("\n✓ All checks passed! OpenCode Ecosystem is healthy.\n");
  exit(0);
} else {
  console.log("\n✗ Some checks failed. Review the output above.\n");
  exit(1);
}