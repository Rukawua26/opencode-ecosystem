import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { lstatSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const skillsCli = join(repoRoot, "tools", "scripts", "skills.js");
let home;

function write(relativePath, content) {
  const path = join(home, relativePath);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content);
  return path;
}

function run(args) {
  return spawnSync(process.execPath, [skillsCli, ...args], {
    encoding: "utf8",
    env: { ...process.env, HOME: home, USERPROFILE: home, NODE_DISABLE_COMPILE_CACHE: "1" },
  });
}

beforeEach(() => {
  home = mkdtempSync(join(tmpdir(), "opencode-skills-"));
  write("opencode-custom/skills/code-review/SKILL.md", [
    "---",
    "name: code-review",
    "description: Reviews code without loading every skill.",
    "---",
    "# Body",
  ].join("\n"));
  write(".opencode/skills/docs/SKILL.md", [
    "---",
    "name: docs-helper",
    "description: >",
    "  Finds and explains",
    "  local documentation.",
    "---",
  ].join("\n"));
  write(".config/opencode/skills/duplicate/SKILL.md", [
    "---",
    "name: code-review",
    "description: Duplicate for detection.",
    "---",
  ].join("\n"));
  write(".config/opencode/skills/invalid/SKILL.md", "# missing frontmatter\n");
  write(".config/opencode/skills/invalid-yaml/SKILL.md", "---\nname: invalid-yaml\ndescription: [broken\n---\n");
});

afterEach(() => rmSync(home, { recursive: true, force: true }));

describe("opencode-skills", () => {
  it("builds a deterministic metadata-only index", () => {
    const result = run(["--refresh"]);
    expect(result.status).toBe(0);
    const indexPath = join(home, ".config", "opencode", ".skills-index.json");
    const index = JSON.parse(readFileSync(indexPath, "utf8"));
    expect(index.schemaVersion).toBe(1);
    expect(index.skills.map((skill) => skill.name)).toEqual(["code-review", "code-review", "docs-helper"]);
    expect(index.skills.every((skill) => !Object.hasOwn(skill, "body"))).toBe(true);
    expect(index.duplicates).toEqual([expect.objectContaining({ name: "code-review" })]);
    expect(index.invalid).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: "frontmatter_missing" }),
      expect.objectContaining({ code: "frontmatter_invalid" }),
    ]));
    expect(Object.keys(index.skills[0]).sort()).toEqual(["description", "name", "path", "root"]);
    expect(lstatSync(indexPath).mode & 0o077).toBe(0);
  });

  it("keeps status, JSON and search read-only", () => {
    expect(run(["--refresh"]).status).toBe(0);
    const indexPath = join(home, ".config", "opencode", ".skills-index.json");
    const before = readFileSync(indexPath, "utf8");
    expect(run(["--status"]).stdout).toContain("Skills: 3");
    expect(JSON.parse(run(["--json"]).stdout).skills).toHaveLength(3);
    expect(run(["--search", "documentation"]).stdout).toContain("docs-helper");
    expect(readFileSync(indexPath, "utf8")).toBe(before);
  });

  it("fails cleanly when the index is missing or search has no match", () => {
    expect(run(["--status"]).status).toBe(1);
    expect(run(["--refresh"]).status).toBe(0);
    expect(run(["--search", "does-not-exist"]).status).toBe(1);
  });

  it.skipIf(process.platform === "win32")("does not follow skill or index symlinks", () => {
    const outside = write("outside/SKILL.md", "---\nname: outside\ndescription: Outside root.\n---\n");
    symlinkSync(dirname(outside), join(home, "opencode-custom", "skills", "linked"), "dir");
    expect(run(["--refresh"]).status).toBe(0);
    const indexPath = join(home, ".config", "opencode", ".skills-index.json");
    expect(readFileSync(indexPath, "utf8")).not.toContain("outside");
    rmSync(indexPath);
    symlinkSync(outside, indexPath);
    expect(run(["--refresh"]).status).toBe(1);
  });

  it.skipIf(process.platform === "win32")("does not follow symlinks in root or index ancestors", () => {
    const outsideRoot = join(home, "outside-root");
    mkdirSync(join(outsideRoot, "skills", "external"), { recursive: true });
    writeFileSync(join(outsideRoot, "skills", "external", "SKILL.md"), "---\nname: external\ndescription: External.\n---\n");
    rmSync(join(home, ".opencode"), { recursive: true, force: true });
    symlinkSync(outsideRoot, join(home, ".opencode"), "dir");
    expect(run(["--refresh"]).status).toBe(0);
    expect(readFileSync(join(home, ".config", "opencode", ".skills-index.json"), "utf8")).not.toContain('"external"');

    rmSync(join(home, ".config"), { recursive: true, force: true });
    symlinkSync(outsideRoot, join(home, ".config"), "dir");
    expect(run(["--refresh"]).status).toBe(1);
  });
});
