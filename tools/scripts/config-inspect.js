import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

export function stripJsonc(text) {
  let withoutComments = "";
  let inString = false;
  let escaped = false;

  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    const next = text[index + 1];
    if (inString) {
      withoutComments += char;
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') {
      inString = true;
      withoutComments += char;
      continue;
    }
    if (char === "/" && next === "/") {
      while (index < text.length && text[index] !== "\n") index++;
      withoutComments += "\n";
      continue;
    }
    if (char === "/" && next === "*") {
      index += 2;
      let closed = false;
      while (index < text.length) {
        if (text[index] === "*" && text[index + 1] === "/") {
          closed = true;
          break;
        }
        index++;
      }
      if (!closed) throw new Error("unterminated_block_comment");
      index++;
      withoutComments += " ";
      continue;
    }
    withoutComments += char;
  }

  let result = "";
  inString = false;
  escaped = false;
  for (let index = 0; index < withoutComments.length; index++) {
    const char = withoutComments[index];
    if (inString) {
      result += char;
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') {
      inString = true;
      result += char;
      continue;
    }
    if (char === ",") {
      let lookahead = index + 1;
      while (/\s/.test(withoutComments[lookahead] || "")) lookahead++;
      if (withoutComments[lookahead] === "}" || withoutComments[lookahead] === "]") continue;
    }
    result += char;
  }
  return result;
}

function pluginNames(entries) {
  if (!Array.isArray(entries)) return [];
  return entries
    .map((entry) => typeof entry === "string" ? entry : Array.isArray(entry) && typeof entry[0] === "string" ? entry[0] : null)
    .filter(Boolean)
    .sort();
}

export function inspectConfigFile(filePath) {
  if (!existsSync(filePath)) return { valid: false, error: "config_missing" };
  try {
    const parsed = JSON.parse(stripJsonc(readFileSync(filePath, "utf8")));
    return {
      valid: true,
      model: parsed.model || null,
      smallModel: parsed.small_model || null,
      plugins: pluginNames(parsed.plugin),
      mcp: parsed.mcp && typeof parsed.mcp === "object" ? Object.keys(parsed.mcp).sort() : [],
      agents: parsed.agent && typeof parsed.agent === "object" ? Object.keys(parsed.agent).sort() : [],
      sddMultiModelPresent: Boolean(parsed.sdd_multi_model),
    };
  } catch {
    return { valid: false, error: "config_unparseable" };
  }
}

function expandConfigPath(configPath, home) {
  if (configPath === "~") return home;
  if (configPath.startsWith("~/") || configPath.startsWith("~\\")) return join(home, configPath.slice(2));
  return resolve(configPath);
}

export function inspectConfiguration({ home, opencodeDir, env = process.env }) {
  const profilesDir = join(opencodeDir, "profiles");
  const mainPath = join(opencodeDir, "opencode.jsonc");
  const main = { path: mainPath, ...inspectConfigFile(mainPath) };
  const profiles = existsSync(profilesDir) && statSync(profilesDir).isDirectory()
    ? readdirSync(profilesDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => {
        const path = join(profilesDir, entry.name, "opencode.jsonc");
        return { name: entry.name, path, ...inspectConfigFile(path) };
      })
      .sort((a, b) => a.name.localeCompare(b.name))
    : [];

  let active = { profile: "default", configPath: mainPath, via: "none" };
  if (env.OPENCODE_CONFIG) {
    const configPath = expandConfigPath(env.OPENCODE_CONFIG, home);
    const relativePath = relative(profilesDir, configPath);
    const first = relativePath.split(/[/\\]/)[0];
    const profile = first && first !== ".." && !relativePath.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`)
      ? first
      : "custom";
    active = { profile, configPath, via: "OPENCODE_CONFIG" };
  }

  const activeConfig = { path: active.configPath, ...inspectConfigFile(active.configPath) };
  const notes = [];
  if (main.sddMultiModelPresent) {
    notes.push("sdd_multi_model is declared but no runtime consumer is confirmed; it remains experimental reference only");
  }
  if (profiles.length === 0) notes.push("no installed profiles were found");
  if (!activeConfig.valid) notes.push(`active profile ${active.profile} is invalid: ${activeConfig.error}`);

  return { active, activeConfig, main, profiles, notes };
}
