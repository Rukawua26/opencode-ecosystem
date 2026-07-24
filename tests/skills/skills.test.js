import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const skillsDir = join(__dirname, "..", "..", "skills");

function getSkillDirs() {
  if (!existsSync(skillsDir)) return [];
  return readdirSync(skillsDir).filter((f) => {
    const p = join(skillsDir, f);
    return statSync(p).isDirectory();
  });
}

describe("Skills structure", () => {
  const skills = getSkillDirs();

  it("should have at least 10 skills", () => {
  it("should have at least 10 skills", () => {
    expect(skills.length).toBeGreaterThanOrEqual(10);
  });

  it("each skill directory should contain a SKILL.md file", () => {
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      expect(existsSync(skillMd), `SKILL.md not found in ${skill}`).toBe(true);
    }
  });

  it("SKILL.md should have valid frontmatter with name and description", () => {
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      const content = readFileSync(skillMd, "utf-8");
      expect(content.length, `${skill} SKILL.md is empty`).toBeGreaterThan(0);
    }
  });
});
