import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
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

function loadSkill(name) {
  const skillMd = join(skillsDir, name, "SKILL.md");
  if (!existsSync(skillMd)) return null;
  const content = readFileSync(skillMd, "utf-8");
  const fm = parseFrontmatter(content);
  return {
    name: fm?.name || name,
    description: fm?.description || "",
    directory: name,
    content,
  };
}

export function listSkills() {
  return getSkillDirs();
}

export function getSkill(name) {
  return loadSkill(name);
}

export function getAllSkills() {
  return getSkillDirs().map(loadSkill).filter(Boolean);
}

export function getSkillContent(name) {
  const skillMd = join(skillsDir, name, "SKILL.md");
  if (!existsSync(skillMd)) return null;
  return readFileSync(skillMd, "utf-8");
}

export default {
  listSkills,
  getSkill,
  getAllSkills,
  getSkillContent,
};
