import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { chmodSync, cpSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const profileScript = join(repoRoot, "tools", "scripts", "profile.js");
const profileLauncher = join(repoRoot, "tools", "scripts", "opencode-profile.sh");
let home;

function write(relativePath, content) {
  const path = join(home, relativePath);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content);
  return path;
}

function runProfile(args = [], extraEnv = {}) {
  return spawnSync(process.execPath, [profileScript, ...args], {
    encoding: "utf8",
    env: { ...process.env, HOME: home, USERPROFILE: home, OPENCODE_CONFIG: "", ...extraEnv },
  });
}

beforeEach(() => {
  home = mkdtempSync(join(tmpdir(), "opencode-profile-"));
  write(".config/opencode/opencode.jsonc", "{ /* supported JSONC */ \"small_model\": \"openai/mini\", }");
  write(".config/opencode/profiles/work/opencode.jsonc", "{ \"model\": \"openai/work\" }");
  write(".config/opencode/profiles/personal/opencode.jsonc", "{ \"model\": \"openai/personal\" }");
  write(".config/opencode/profiles/light/opencode.jsonc", "{ \"model\": \"openai/light\" }");
});

afterEach(() => rmSync(home, { recursive: true, force: true }));

describe("profile inspector and launchers", () => {
  it("reports deterministic profiles without writing", () => {
    const before = readdirSync(home, { recursive: true }).sort();
    const result = runProfile(["--json"]);
    expect(result.status).toBe(0);
    const report = JSON.parse(result.stdout);
    expect(report.active.profile).toBe("default");
    expect(report.main.smallModel).toBe("openai/mini");
    expect(report.profiles.map((profile) => profile.name)).toEqual(["light", "personal", "work"]);
    expect(readdirSync(home, { recursive: true }).sort()).toEqual(before);
  });

  it("detects the active profile from OPENCODE_CONFIG", () => {
    const config = join(home, ".config", "opencode", "profiles", "light", "opencode.jsonc");
    const result = runProfile(["--json"], { OPENCODE_CONFIG: config });
    expect(JSON.parse(result.stdout).active).toMatchObject({ profile: "light", via: "OPENCODE_CONFIG" });
  });

  it("inspects the exact active config path instead of the canonical profile file", () => {
    const config = write(".config/opencode/profiles/light/alternate.jsonc", "invalid");
    const result = runProfile(["--json"], { OPENCODE_CONFIG: config });
    const report = JSON.parse(result.stdout);
    expect(report.active).toMatchObject({ profile: "light", configPath: config });
    expect(report.notes).toEqual(expect.arrayContaining([expect.stringContaining("active profile light is invalid")]));
  });

  it("rejects unterminated JSONC block comments", () => {
    write(".config/opencode/profiles/light/opencode.jsonc", "{ \"model\": \"openai/light\" } /*");
    expect(runProfile(["--validate", "light"]).status).toBe(1);
  });

  it("fails validation for missing or invalid profiles", () => {
    expect(runProfile(["--validate", "missing"]).status).toBe(1);
    write(".config/opencode/profiles/light/opencode.jsonc", "invalid");
    expect(runProfile(["--validate", "light"]).status).toBe(1);
  });

  it.skipIf(process.platform === "win32")("launches OpenCode with the selected profile and effort", () => {
    const tools = join(home, ".config", "opencode", "tools");
    mkdirSync(tools, { recursive: true });
    cpSync(profileScript, join(tools, "profile.js"));
    cpSync(join(repoRoot, "tools", "scripts", "config-inspect.js"), join(tools, "config-inspect.js"));
    const fakeBin = join(home, "bin");
    mkdirSync(fakeBin);
    const output = join(home, "launch.txt");
    const fakeOpenCode = write("bin/opencode", `#!/usr/bin/env bash\nprintf '%s|%s|%s' "$OPENCODE_CONFIG" "$OPENCODE_EFFORT_MODE" "$*" > "${output}"\n`);
    chmodSync(fakeOpenCode, 0o755);
    const result = spawnSync("bash", [profileLauncher, "light", "--test-arg"], {
      encoding: "utf8",
      env: { ...process.env, HOME: home, USERPROFILE: home, PATH: `${fakeBin}:${process.env.PATH}` },
    });
    expect(result.status).toBe(0);
    expect(readFileSync(output, "utf8")).toBe(`${join(home, ".config/opencode/profiles/light/opencode.jsonc")}|low|--test-arg`);
  });
});
