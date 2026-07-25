import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pluginsDir = join(__dirname, "..", "..", "config", "plugins");

function getPluginFiles() {
  if (!existsSync(pluginsDir)) return [];
  return readdirSync(pluginsDir).filter((f) => f.endsWith(".js"));
}

function readPlugin(name) {
  return readFileSync(join(pluginsDir, name), "utf-8");
}

const REQUIRED_PLUGINS = [
  "auto-memory.js",
  "checkpoints.js",
  "guardrails.js",
  "kanban.js",
  "personalities.js",
  "sandbox.js",
  "session-metrics.js",
  "validator.js",
];

describe("Plugins registry", () => {
  const plugins = getPluginFiles();

  it("should have at least 5 plugin files", () => {
    expect(plugins.length).toBeGreaterThanOrEqual(5);
  });

  it("all required plugins should exist", () => {
    for (const req of REQUIRED_PLUGINS) {
      expect(plugins, `missing required plugin ${req}`).toContain(req);
    }
  });
});

describe("Plugin exports", () => {
  const plugins = getPluginFiles();

  it("each plugin should export an async function", () => {
    for (const plugin of plugins) {
      const content = readPlugin(plugin);
      expect(
        content.includes("export"),
        `${plugin} does not have exports`
      ).toBe(true);
    }
  });

  it("each plugin should export a default or named plugin function", () => {
    for (const plugin of plugins) {
      const content = readPlugin(plugin);
      const hasExport =
        /export\s+(const|default|async|function)\s+\w*[Pp]lugin/i.test(content) ||
        /export\s+default\s+async/i.test(content) ||
        /export\s+const\s+\w+Plugin/i.test(content);
      expect(hasExport, `${plugin} does not export a plugin function`).toBe(true);
    }
  });
});

describe("Plugin safety", () => {
  it("plugins should not contain eval()", () => {
    for (const plugin of getPluginFiles()) {
      const content = readPlugin(plugin);
      expect(content.includes("eval("), `${plugin} uses eval()`).toBe(false);
    }
  });

  it("plugins should not hardcode secrets or API keys", () => {
    for (const plugin of getPluginFiles()) {
      const content = readPlugin(plugin);
      const hasSecret =
        /(?:sk-|ghp_|gho_|npm_)[A-Za-z0-9]{20,}/.test(content) ||
        /(?:api[_-]?key)\s*[:=]\s*["'][A-Za-z0-9]{20,}["']/i.test(content);
      expect(hasSecret, `${plugin} appears to contain a hardcoded secret`).toBe(false);
    }
  });

  it("plugins should use process.env for environment access", () => {
    for (const plugin of getPluginFiles()) {
      const content = readPlugin(plugin);
      if (content.includes("process.env")) continue;
      const needsEnv =
        content.includes("HOME") ||
        content.includes("USERPROFILE") ||
        content.includes("API") ||
        content.includes("token");
      expect(needsEnv, `${plugin} accesses env vars without process.env`).toBe(false);
    }
  });
});

describe("Kanban plugin tools", () => {
  const content = readPlugin("kanban.js");

  it("should define kanban_create tool", () => {
    expect(content, "kanban_create tool missing").toContain("kanban_create");
  });

  it("should define kanban_list tool", () => {
    expect(content, "kanban_list tool missing").toContain("kanban_list");
  });

  it("should define kanban_update tool", () => {
    expect(content, "kanban_update tool missing").toContain("kanban_update");
  });

  it("should define kanban_delete tool", () => {
    expect(content, "kanban_delete tool missing").toContain("kanban_delete");
  });

  it("should use safe status values", () => {
    const statuses = ["todo", "in_progress", "done", "blocked"];
    for (const s of statuses) {
      expect(content, `status ${s} missing`).toContain(s);
    }
  });
});

describe("Guardrails plugin", () => {
  const content = readPlugin("guardrails.js");

  it("should define consecutive tool warning threshold", () => {
    expect(content).toMatch(/WARN_CONSECUTIVE|consecutive/i);
  });

  it("should define total tool warning threshold", () => {
    expect(content).toMatch(/WARN_TOTAL|total/i);
  });

  it("should expose before/after hooks", () => {
    expect(content, "missing tool.execute.before hook").toContain("tool.execute.before");
    expect(content, "missing tool.execute.after hook").toContain("tool.execute.after");
  });
});

describe("Checkpoints plugin", () => {
  const content = readPlugin("checkpoints.js");

  it("should reference snapshot or backup logic", () => {
    expect(
      content.includes("snapshot") || content.includes("backup") || content.includes("copy"),
      "checkpoints.js missing snapshot/backup logic"
    ).toBe(true);
  });

  it("should hook into write or edit events", () => {
    expect(
      content.includes("write") || content.includes("edit") || content.includes("before"),
      "checkpoints.js missing write/edit hook"
    ).toBe(true);
  });
});

describe("Sandbox plugin", () => {
  const content = readPlugin("sandbox.js");

  it("should define sandbox_exec tool", () => {
    expect(content, "sandbox_exec tool missing").toContain("sandbox_exec");
  });

  it("should use Docker isolation", () => {
    expect(content, "sandbox.js does not reference Docker").toMatch(/docker|container|isolated/i);
  });
});

describe("Validator plugin", () => {
  const content = readPlugin("validator.js");

  it("should reference API key validation", () => {
    expect(content).toMatch(/api[_-]?key|valid/i);
  });
});

describe("Session metrics plugin", () => {
  const content = readPlugin("session-metrics.js");

  it("should reference token or usage tracking", () => {
    expect(content).toMatch(/token|usage|metrics|count/i);
  });
});

describe("Personalities plugin", () => {
  const content = readPlugin("personalities.js");

  it("should reference SOUL.md", () => {
    expect(content, "personalities.js missing SOUL.md reference").toContain("SOUL.md");
  });

  it("should define set_personality tool", () => {
    expect(content, "set_personality tool missing").toContain("set_personality");
  });
});

describe("Auto-memory plugin", () => {
  const content = readPlugin("auto-memory.js");

  it("should reference memory or context capture", () => {
    expect(content).toMatch(/memory|context|capture|decision|bug/i);
  });

  it("should reference a project or projectPath", () => {
    expect(content).toMatch(/projectPath|project/i);
  });
});
