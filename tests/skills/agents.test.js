import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const agentsDir = join(__dirname, "..", "..", "config", "agents");

function getAgentFiles() {
  if (!existsSync(agentsDir)) return [];
  return readdirSync(agentsDir).filter((f) => f.endsWith(".md"));
}

describe("Agents structure", () => {
  const agents = getAgentFiles();

  it("should have at least 10 agent definitions", () => {
    expect(agents.length).toBeGreaterThanOrEqual(10);
  });

  it("each agent file should have substantial content", () => {
    for (const agent of agents) {
      const content = readFileSync(join(agentsDir, agent), "utf-8");
      expect(content.length, `${agent} is too small`).toBeGreaterThan(100);
    }
  });
});
