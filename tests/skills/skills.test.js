import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const skillsDir = join(__dirname, "..", "..", "skills");

function getSkillDirs() {
  if (!existsSync(skillsDir)) return [];
  return readdirSync(skillsDir).filter((f) => {
    if (f.startsWith("zz-test-")) return false;
    try {
      const p = join(skillsDir, f);
      return statSync(p).isDirectory();
    } catch {
      return false;
    }
  });
}

function parseFrontmatter(content) {
  const match = content.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return null;
  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    const field = line.match(/^(\w+):\s*(.+)$/);
    if (field) fields[field[1]] = field[2].replace(/^["']|["']$/g, "");
  }
  return fields;
}

describe("Skills structure", () => {
  const skills = getSkillDirs();

  it("should have at least 10 skills", () => {
    expect(skills.length).toBeGreaterThanOrEqual(10);
  });

  it("each skill directory should contain a SKILL.md file", () => {
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      expect(existsSync(skillMd), `SKILL.md not found in ${skill}`).toBe(true);
    }
  });

  it("SKILL.md should be non-empty and have complete frontmatter when present", () => {
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      const content = readFileSync(skillMd, "utf-8");
      expect(content.length, `${skill} SKILL.md is empty`).toBeGreaterThan(0);
      const frontmatter = parseFrontmatter(content);
      if (frontmatter) {
        expect(frontmatter.name, `${skill} frontmatter missing name`).toBeTruthy();
        expect(frontmatter.description, `${skill} frontmatter missing description`).toBeTruthy();
      }
    }
  });
});

describe("obsidian-ingest contract", () => {
  const sourceSkill = join(skillsDir, "obsidian-ingest", "SKILL.md");
  const packageSkill = join(__dirname, "..", "..", "packages", "skills", "skills", "obsidian-ingest", "SKILL.md");

  it("is mirrored into the npm skills package", () => {
    expect(existsSync(sourceSkill)).toBe(true);
    expect(existsSync(packageSkill)).toBe(true);
    const content = readFileSync(sourceSkill, "utf-8");
    expect(readFileSync(packageSkill, "utf-8")).toBe(content);
    expect(parseFrontmatter(content)?.name).toBe("obsidian-ingest");
    expect(parseFrontmatter(content)?.description).toBeTruthy();
  });

  it("keeps ingestion bounded, local-first, and preview-only by default", () => {
    const content = readFileSync(sourceSkill, "utf-8");
    expect(content).toContain("ask_chat_model");
    expect(content).toMatch(/five related notes/i);
    expect(content).toMatch(/untrusted data/i);
    expect(content).toMatch(/preview/i);
    expect(content).toMatch(/never overwrite/i);
    expect(content).toMatch(/shell-safe argv/i);
    expect(content).toMatch(/confine.*vault/i);
  });
});
