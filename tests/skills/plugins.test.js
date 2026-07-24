import { describe, it, expect } from "vitest";
import { existsSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pluginsDir = join(__dirname, "..", "..", "config", "plugins");

function getPluginFiles() {
  if (!existsSync(pluginsDir)) return [];
  return readdirSync(pluginsDir).filter((f) => f.endsWith(".js"));
}

describe("Plugins structure", () => {
  const plugins = getPluginFiles();

  it("should have at least 5 plugin files", () => {
    expect(plugins.length).toBeGreaterThanOrEqual(5);
  });

  it("each plugin should export something", () => {
    for (const plugin of plugins) {
      const content = readFileSync(join(pluginsDir, plugin), "utf-8");
      expect(
        content.includes("export"),
        `${plugin} does not have exports`
      ).toBe(true);
    }
  });
});
