#!/usr/bin/env node
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const SYSTEMCTL = "/usr/bin/systemctl";
const OLLAMA_URL = "http://127.0.0.1:11434";

async function serviceActive() {
  try {
    await execFileAsync(SYSTEMCTL, ["--user", "is-active", "--quiet", "ollama.service"], {
      timeout: 5_000,
    });
    return true;
  } catch {
    return false;
  }
}

async function stopIdleTimer() {
  await execFileAsync(SYSTEMCTL, ["--user", "stop", "ollama-idle-stop.timer"], { timeout: 5_000 });
}

async function runningModels() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2_000);
  try {
    const response = await fetch(`${OLLAMA_URL}/api/ps`, { signal: controller.signal });
    if (!response.ok) return 1;
    const payload = await response.json();
    return Array.isArray(payload.models) ? payload.models.length : 1;
  } catch {
    return 1;
  } finally {
    clearTimeout(timer);
  }
}

async function main() {
  if (!(await serviceActive())) {
    await stopIdleTimer();
    return;
  }
  if ((await runningModels()) > 0) return;
  await execFileAsync(SYSTEMCTL, ["--user", "stop", "ollama.service"], { timeout: 15_000 });
  await stopIdleTimer();
}

main().catch((error) => {
  process.stderr.write(`ollama idle stop failed: ${error instanceof Error ? error.message : "unknown"}\n`);
  process.exitCode = 1;
});
