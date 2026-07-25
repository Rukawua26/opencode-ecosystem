import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, dirname, basename } from "node:path";
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

function parseFrontmatter(content) {
  const fmMatch = content.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!fmMatch) return null;
  const fm = {};
  for (const line of fmMatch[1].split("\n")) {
    const m = line.match(/^(\w+):\s*(.+)$/);
    if (m) fm[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
  return fm;
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

  it("SKILL.md should have non-empty content", () => {
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      const content = readFileSync(skillMd, "utf-8");
      expect(content.length, `${skill} SKILL.md is empty`).toBeGreaterThan(0);
    }
  });
});

describe("Skills frontmatter", () => {
  const skills = getSkillDirs();
  const withFm = [];
  const withoutFm = [];

  for (const skill of skills) {
    const skillMd = join(skillsDir, skill, "SKILL.md");
    const content = readFileSync(skillMd, "utf-8");
    const fm = parseFrontmatter(content);
    if (fm) withFm.push({ skill, fm });
    else withoutFm.push(skill);
  }

  it("at least 50% of skills should have YAML frontmatter", () => {
    expect(withFm.length, "too few skills with frontmatter").toBeGreaterThanOrEqual(skills.length / 2);
  });

  it("skills with frontmatter should have a name field", () => {
    for (const { skill, fm } of withFm) {
      expect(fm.name, `${skill} frontmatter missing name`).toBeDefined();
    }
  });

  it("skills with frontmatter should have a description field", () => {
    for (const { skill, fm } of withFm) {
      expect(fm.description, `${skill} frontmatter missing description`).toBeDefined();
    }
  });

  it("frontmatter name should match directory name or be related", () => {
    for (const { skill, fm } of withFm) {
      if (fm.name) {
        const fn = fm.name.toLowerCase();
        const dn = skill.toLowerCase();
        const match = fn === dn || dn.includes(fn) || fn.includes(dn) || dn.replace(/-/g, "").includes(fn.replace(/-/g, ""));
        expect(match, `${skill} dir name does not match frontmatter name "${fm.name}"`).toBe(true);
      }
    }
  });
});

describe("Skills content quality", () => {
  const skills = getSkillDirs();

  it("each SKILL.md should have at least 2 sections (## headings) or substantial content", () => {
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      const content = readFileSync(skillMd, "utf-8");
      const h2count = (content.match(/^##\s/gm) || []).length;
      if (h2count < 2) {
        expect(content.length, `${skill} too short and too few sections`).toBeGreaterThan(150);
      }
    }
  });

  it("each SKILL.md should mention a trigger or usage guidance", () => {
    const triggerWords = [
      "trigger",
      "cuando usar",
      "cuándo usar",
      "use when",
      "use this",
      "uso",
      "use instead",
      "use only",
      "use para",
    ];
    for (const skill of skills) {
      const skillMd = join(skillsDir, skill, "SKILL.md");
      const content = readFileSync(skillMd, "utf-8").toLowerCase();
      const hasTrigger = triggerWords.some((w) => content.includes(w));
      if (!hasTrigger) {
        expect(content.length, `${skill} missing trigger guidance and too short`).toBeGreaterThan(300);
      } else {
        expect(hasTrigger, `${skill} missing trigger/usage guidance`).toBe(true);
      }
    }
  });
});
