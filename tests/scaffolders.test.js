import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..");
const describePosix = process.platform === "win32" ? describe.skip : describe;
const executionOptions = { timeout: 5_000, stdio: "pipe" };
let testRoot;

function scaffoldScript(name) {
  return join(testRoot, "tools", "scripts", name);
}

function runScaffolder(script, ...args) {
  return execFileSync("bash", [scaffoldScript(script), ...args], {
    cwd: testRoot,
    ...executionOptions,
  });
}

function expectExitOne(callback) {
  let executionError;
  try {
    callback();
  } catch (error) {
    executionError = error;
  }
  expect(executionError).toBeDefined();
  expect(executionError.status).toBe(1);
  return executionError;
}

beforeEach(() => {
  testRoot = undefined;
  testRoot = mkdtempSync(join(tmpdir(), "opencode-scaffolders-"));
  mkdirSync(join(testRoot, "tools", "scripts"), { recursive: true });
  mkdirSync(join(testRoot, "config", "plugins"), { recursive: true });
  for (const script of ["create-skill.sh", "create-plugin.sh"]) {
    copyFileSync(join(repoRoot, "tools", "scripts", script), scaffoldScript(script));
  }
});

afterEach(() => {
  if (testRoot) rmSync(testRoot, { recursive: true, force: true });
});

describePosix("create-skill.sh scaffolder", () => {
  const skillName = "zz-test-scaffold-skill";

  it("should create a skill directory with SKILL.md", () => {
    const skillDir = join(testRoot, "skills", skillName);
    runScaffolder("create-skill.sh", skillName);
    expect(existsSync(skillDir)).toBe(true);
    expect(existsSync(join(skillDir, "SKILL.md"))).toBe(true);
  });

  it("SKILL.md should have valid frontmatter with name and description", () => {
    const skillDir = join(testRoot, "skills", skillName);
    runScaffolder("create-skill.sh", skillName);
    const content = readFileSync(join(skillDir, "SKILL.md"), "utf8");
    expect(content).toContain("---");
    expect(content).toContain(`name: ${skillName}`);
    expect(content).toContain("description:");
  });

  it("should fail if skill already exists", () => {
    runScaffolder("create-skill.sh", skillName);
    const error = expectExitOne(() => runScaffolder("create-skill.sh", skillName));
    expect(error.stdout.toString()).toContain("already exists");
  });

  it("should fail without skill name argument", () => {
    const error = expectExitOne(() => runScaffolder("create-skill.sh"));
    expect(error.stdout.toString()).toContain("Usage:");
  });

  it.each(["../escape", "Invalid Name", "name_with_underscore", "skill-2"])("should reject unsafe skill name %s", (invalidName) => {
    const error = expectExitOne(() => runScaffolder("create-skill.sh", invalidName));
    expect(error.stdout.toString()).toContain("lowercase kebab-case");
    expect(existsSync(join(testRoot, "skills"))).toBe(false);
  });
});

describePosix("create-plugin.sh scaffolder", () => {
  const pluginName = "zz-test-scaffold-plugin";

  it("should create a plugin .js file", () => {
    const pluginFile = join(testRoot, "config", "plugins", `${pluginName}.js`);
    runScaffolder("create-plugin.sh", pluginName);
    expect(existsSync(pluginFile)).toBe(true);
  });

  it("generated plugin should use valid JS identifiers (camelCase)", () => {
    const pluginFile = join(testRoot, "config", "plugins", `${pluginName}.js`);
    runScaffolder("create-plugin.sh", pluginName);
    const content = readFileSync(pluginFile, "utf8");
    expect(content).toContain("import { tool }");
    expect(content).toMatch(/export const zzTestScaffoldPlugin/);
    expect(content).not.toMatch(/export const zz-test-scaffold-plugin/);
  });

  it("should fail if plugin already exists", () => {
    runScaffolder("create-plugin.sh", pluginName);
    const error = expectExitOne(() => runScaffolder("create-plugin.sh", pluginName));
    expect(error.stdout.toString()).toContain("already exists");
  });

  it("should fail without plugin name argument", () => {
    const error = expectExitOne(() => runScaffolder("create-plugin.sh"));
    expect(error.stdout.toString()).toContain("Usage:");
  });

  it.each(["../escape", "Invalid Name", "plugin-2", "x';process.exit(0);//"])("should reject unsafe plugin name %s", (invalidName) => {
    const error = expectExitOne(() => runScaffolder("create-plugin.sh", invalidName));
    expect(error.stdout.toString()).toContain("lowercase kebab-case");
    expect(existsSync(join(testRoot, "config", "escape.js"))).toBe(false);
    expect(readdirSync(join(testRoot, "config", "plugins"))).toHaveLength(0);
  });

  it.each(["class", "arguments", "interface"])("should reject reserved JavaScript word %s", (reservedWord) => {
    const error = expectExitOne(() => runScaffolder("create-plugin.sh", reservedWord));
    expect(error.stdout.toString()).toContain("reserved JavaScript word");
    expect(readdirSync(join(testRoot, "config", "plugins"))).toHaveLength(0);
  });

  it("should reject dangling symbolic links at the destination", () => {
    const pluginFile = join(testRoot, "config", "plugins", `${pluginName}.js`);
    const escapedFile = join(testRoot, "escaped-plugin.js");
    symlinkSync(escapedFile, pluginFile);

    const error = expectExitOne(() => runScaffolder("create-plugin.sh", pluginName));
    expect(error.stdout.toString()).toContain("already exists");
    expect(existsSync(escapedFile)).toBe(false);
  });
});
