#!/usr/bin/env node

import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const HOME = process.env.HOME || process.env.USERPROFILE || "/tmp";
const OPENCODE_DIR = join(HOME, ".config", "opencode");
const DATA_DIR = join(HOME, ".local", "share", "opencode", "plugins-data");

let checks = 0;
let passed = 0;

function check(name, test) {
  checks++;
  try {
    if (test()) {
      passed++;
      console.log(`[OK] ${name}`);
      return;
    }
    console.log(`[FAIL] ${name}`);
  } catch (error) {
    console.log(`[ERROR] ${name}: ${error.message}`);
  }
}

function optional(name, test) {
  try {
    console.log(test() ? `[OK] ${name}` : `[SKIP] ${name}`);
  } catch {
    console.log(`[SKIP] ${name}`);
  }
}

function commandWorks(command, args = ["--version"]) {
  return spawnSync(command, args, { stdio: "ignore", timeout: 5000 }).status === 0;
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

console.log("\n=== OpenCode Ecosystem Doctor ===\n");

console.log("--- Runtime ---");
check("Node.js >= 22", () => Number(process.versions.node.split(".")[0]) >= 22);
check("npm available", () => commandWorks("npm"));
check("git available", () => commandWorks("git"));

console.log("\n--- OpenCode ---");
check("opencode.jsonc", () => existsSync(join(OPENCODE_DIR, "opencode.jsonc")));
for (const directory of ["agents", "plugins", "mcp", "profiles"]) {
  check(`${directory} directory`, () => {
    const path = join(OPENCODE_DIR, directory);
    return existsSync(path) && statSync(path).isDirectory();
  });
}
check("skills directory", () => existsSync(join(HOME, "opencode-custom", "skills")));
check("plugins-data directory", () => existsSync(DATA_DIR));

console.log("\n--- Memory adapter ---");
const memoryDir = join(OPENCODE_DIR, "mcp", "memory-adapter");
for (const file of ["package.json", join("src", "adapter.js"), join("src", "mcp-server.js"), join("src", "cli.js")]) {
  check(`memory-adapter/${file}`, () => existsSync(join(memoryDir, file)));
}

console.log("\n--- Optional services ---");
optional("Ollama server", () => commandWorks("ollama", ["list"]));
optional("opencode-doctor installed", () => {
  const suffix = process.platform === "win32" ? ".cmd" : "";
  return existsSync(join(HOME, ".opencode", "bin", `opencode-doctor${suffix}`));
});

console.log("\n--- Providers ---");
const environment = parseEnv(join(OPENCODE_DIR, ".env"));
const providers = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"];
check("at least one provider key configured", () => providers.some((key) => Boolean(environment[key] || process.env[key])));

console.log("\n=== Summary ===");
console.log(`Checks: ${passed}/${checks} passed`);
process.exitCode = passed === checks ? 0 : 1;
