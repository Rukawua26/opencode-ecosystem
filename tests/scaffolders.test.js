import { describe, it, expect, afterEach } from "vitest";
import { execSync } from "node:child_process";
import { existsSync, readFileSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..");

describe("create-skill.sh scaffolder", () => {
  const skillName = "zz-test-scaffold-skill";
  const skillDir = join(repoRoot, "skills", skillName);

  afterEach(() => {
    if (existsSync(skillDir)) rmSync(skillDir, { recursive: true, force: true });
  });

  it("should create a skill directory with SKILL.md", () => {
    execSync(`bash ${join(repoRoot, "tools", "scripts", "create-skill.sh")} ${skillName}`, { cwd: repoRoot });
    expect(existsSync(skillDir)).toBe(true);
    expect(existsSync(join(skillDir, "SKILL.md"))).toBe(true);
  });

  it("SKILL.md should have valid frontmatter with name and description", () => {
    execSync(`bash ${join(repoRoot, "tools", "scripts", "create-skill.sh")} ${skillName}`, { cwd: repoRoot });
    const content = readFileSync(join(skillDir, "SKILL.md"), "utf8");
    expect(content).toContain("---");
    expect(content).toContain(`name: ${skillName}`);
    expect(content).toContain("description:");
  });

  it("should fail if skill already exists", () => {
    execSync(`bash ${join(repoRoot, "tools", "scripts", "create-skill.sh")} ${skillName}`, { cwd: repoRoot });
    expect(() => {
      execSync(`bash ${join(repoRoot, "tools", "scripts", "create-skill.sh")} ${skillName}`, { cwd: repoRoot, stdio: "pipe" });
    }).toThrow();
  });

  it("should fail without skill name argument", () => {
    expect(() => {
      execSync(`bash ${join(repoRoot, "tools", "scripts", "create-skill.sh")}`, { cwd: repoRoot, stdio: "pipe" });
    }).toThrow();
  });
});

describe("create-plugin.sh scaffolder", () => {
  const pluginName = "zz-test-scaffold-plugin";
  const pluginFile = join(repoRoot, "config", "plugins", `${pluginName}.js`);

  afterEach(() => {
    if (existsSync(pluginFile)) rmSync(pluginFile, { force: true });
  });

  it("should create a plugin .js file", () => {
    execSync(`bash ${join(repoRoot, "tools", "scripts", "create-plugin.sh")} ${pluginName}`, { cwd: repoRoot });
    expect(existsSync(pluginFile)).toBe(true);
  });

  it("generated plugin should use valid JS identifiers (camelCase)", () => {
    execSync(`bash ${join(repoRoot, "tools", "scripts", "create-plugin.sh")} ${pluginName}`, { cwd: repoRoot });
    const content = readFileSync(pluginFile, "utf8");
    expect(content).toContain("import { tool }");
    expect(content).toMatch(/export const zzTestScaffoldPlugin/);
    expect(content).not.toMatch(/export const zz-test-scaffold-plugin/);
  });

  it("should fail if plugin already exists", () => {
    execSync(`bash ${join(repoRoot, "tools", "scripts", "create-plugin.sh")} ${pluginName}`, { cwd: repoRoot });
    expect(() => {
      execSync(`bash ${join(repoRoot, "tools", "scripts", "create-plugin.sh")} ${pluginName}`, { cwd: repoRoot, stdio: "pipe" });
    }).toThrow();
  });

  it("should fail without plugin name argument", () => {
    expect(() => {
      execSync(`bash ${join(repoRoot, "tools", "scripts", "create-plugin.sh")}`, { cwd: repoRoot, stdio: "pipe" });
    }).toThrow();
  });
});
