#!/usr/bin/env node

import {
  existsSync,
  closeSync,
  lstatSync,
  mkdirSync,
  openSync,
  readSync,
  readFileSync,
  readdirSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const invokedDirectly = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (!invokedDirectly) {
  // Este archivo vive en ~/.config/opencode/tools/, que OpenCode importa como
  // módulo de herramientas en el arranque. Importado no debe ejecutar CLI ni salir.
} else {
  main();
}

function main() {

  const args = process.argv.slice(2);
  const HOME = process.env.HOME || process.env.USERPROFILE || "/tmp";
  const INDEX_PATH = join(HOME, ".config", "opencode", ".skills-index.json");
  const ROOTS = [
    join(HOME, ".config", "opencode", "skills"),
    join(HOME, "opencode-custom", "skills"),
    join(HOME, ".opencode", "skills"),
  ];
  const MAX_FRONTMATTER_BYTES = 64 * 1024;

  function usage(exitCode = 0) {
    const output = exitCode === 0 ? console.log : console.error;
    output("Usage: opencode-skills [--refresh|--status|--json|--search <query>]");
    process.exit(exitCode);
  }

  if (args.includes("--help") || args.includes("-h")) usage();
  const action = args[0] || "--status";
  if (!new Set(["--refresh", "--status", "--json", "--search"]).has(action)) usage(2);
  if (action === "--search" && (!args[1] || args.length !== 2)) usage(2);
  if (action !== "--search" && args.length !== 1 && args.length !== 0) usage(2);

  function parseScalar(value) {
    const trimmed = value.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith('"')) {
      if (!trimmed.endsWith('"')) return null;
      try {
        const parsed = JSON.parse(trimmed);
        return typeof parsed === "string" ? parsed.trim() : null;
      } catch {
        return null;
      }
    }
    if (trimmed.startsWith("'")) return trimmed.endsWith("'") ? trimmed.slice(1, -1).replaceAll("''", "'").trim() : null;
    if (new Set(["[", "]", "{", "&", "*", "!", "?"]).has(trimmed[0]) || /:\s/.test(trimmed)) return null;
    return trimmed;
  }

  function parseFrontmatter(filePath) {
    const descriptor = openSync(filePath, "r");
    const buffer = Buffer.alloc(MAX_FRONTMATTER_BYTES);
    let bytesRead;
    try {
      bytesRead = readSync(descriptor, buffer, 0, buffer.length, 0);
    } finally {
      closeSync(descriptor);
    }
    const content = buffer.subarray(0, bytesRead).toString("utf8");
    const lines = content.split(/\r?\n/);
    if (lines[0]?.trim() !== "---") return { valid: false, code: "frontmatter_missing" };
    const end = lines.findIndex((line, index) => index > 0 && line.trim() === "---");
    if (end === -1) return { valid: false, code: bytesRead === MAX_FRONTMATTER_BYTES ? "frontmatter_too_large" : "frontmatter_unclosed" };

    let name = "";
    let description = "";
    for (let index = 1; index < end; index++) {
      const nameMatch = lines[index].match(/^name:\s*(.*)$/);
      if (nameMatch) {
        const parsed = parseScalar(nameMatch[1]);
        if (parsed === null) return { valid: false, code: "frontmatter_invalid" };
        name = parsed;
      }
      const descriptionMatch = lines[index].match(/^description:\s*(.*)$/);
      if (!descriptionMatch) continue;
      const value = descriptionMatch[1].trim();
      if (value === ">" || value === "|") {
        const parts = [];
        while (index + 1 < end && /^\s+/.test(lines[index + 1])) parts.push(lines[++index].trim());
        description = parts.join(value === ">" ? " " : "\n").trim();
      } else {
        const parsed = parseScalar(value);
        if (parsed === null) return { valid: false, code: "frontmatter_invalid" };
        description = parsed;
      }
    }
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name)) return { valid: false, code: "name_invalid" };
    if (!description) return { valid: false, code: "description_missing" };
    return { valid: true, name, description };
  }

  function tryLstat(path) {
    try {
      return lstatSync(path);
    } catch (error) {
      if (error.code === "ENOENT" || error.code === "ENOTDIR") return null;
      throw error;
    }
  }

  function hasSymlinkComponent(path, root = HOME) {
    const normalizedRoot = resolve(root);
    const normalizedPath = resolve(path);
    const pathFromRoot = relative(normalizedRoot, normalizedPath);
    if (pathFromRoot === ".." || pathFromRoot.startsWith(`..${sep}`)) return true;
    let current = normalizedRoot;
    for (const segment of pathFromRoot.split(sep).filter(Boolean)) {
      current = join(current, segment);
      const stats = tryLstat(current);
      if (!stats) return false;
      if (stats.isSymbolicLink()) return true;
    }
    return false;
  }

  function scanRoot(root, skills, invalid) {
    if (!existsSync(root)) return;
    if (hasSymlinkComponent(root)) return;
    function walk(directory) {
      for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
        if (entry.isSymbolicLink()) continue;
        const path = join(directory, entry.name);
        if (entry.isDirectory()) {
          walk(path);
          continue;
        }
        if (!entry.isFile() || entry.name !== "SKILL.md") continue;
        const parsed = parseFrontmatter(path);
        if (!parsed.valid) {
          invalid.push({ path, code: parsed.code });
          continue;
        }
        skills.push({ name: parsed.name, description: parsed.description, path, root });
      }
    }
    walk(root);
  }

  function buildIndex() {
    const skills = [];
    const invalid = [];
    for (const root of ROOTS) scanRoot(root, skills, invalid);
    skills.sort((a, b) => a.name.localeCompare(b.name) || a.path.localeCompare(b.path));
    invalid.sort((a, b) => a.path.localeCompare(b.path) || a.code.localeCompare(b.code));
    const byName = new Map();
    for (const skill of skills) {
      const paths = byName.get(skill.name) || [];
      paths.push(skill.path);
      byName.set(skill.name, paths);
    }
    const duplicates = [...byName.entries()]
      .filter(([, paths]) => paths.length > 1)
      .map(([name, paths]) => ({ name, paths: paths.sort() }))
      .sort((a, b) => a.name.localeCompare(b.name));
    return { schemaVersion: 1, roots: ROOTS, skills, duplicates, invalid };
  }

  function readIndex() {
    if (!existsSync(INDEX_PATH)) {
      console.error(`Skill index not found: ${INDEX_PATH}. Run opencode-skills --refresh.`);
      process.exit(1);
    }
    try {
      return JSON.parse(readFileSync(INDEX_PATH, "utf8"));
    } catch {
      console.error(`Skill index is invalid: ${INDEX_PATH}. Run opencode-skills --refresh.`);
      process.exit(1);
    }
  }

  function printStatus(index) {
    console.log("=== OpenCode Skill Registry ===");
    console.log(`Index: ${INDEX_PATH}`);
    console.log(`Skills: ${index.skills.length}`);
    console.log(`Duplicates: ${index.duplicates.length}`);
    console.log(`Invalid: ${index.invalid.length}`);
  }

  function terminalSafe(value) {
    return [...String(value)]
      .map((char) => {
        const code = char.codePointAt(0);
        return code < 32 || (code >= 127 && code <= 159) ? " " : char;
      })
      .join("")
      .replace(/\s+/g, " ")
      .trim();
  }

  if (action === "--refresh") {
    if (hasSymlinkComponent(dirname(INDEX_PATH)) || (existsSync(INDEX_PATH) && lstatSync(INDEX_PATH).isSymbolicLink())) {
      console.error(`Refusing to replace symbolic-link index: ${INDEX_PATH}`);
      process.exit(1);
    }
    const index = buildIndex();
    mkdirSync(dirname(INDEX_PATH), { recursive: true });
    const next = `${INDEX_PATH}.next-${process.pid}`;
    try {
      writeFileSync(next, `${JSON.stringify(index, null, 2)}\n`, { mode: 0o600 });
      renameSync(next, INDEX_PATH);
    } finally {
      if (existsSync(next)) unlinkSync(next);
    }
    printStatus(index);
  } else if (action === "--json") {
    console.log(JSON.stringify(readIndex(), null, 2));
  } else if (action === "--search") {
    const query = args[1].toLowerCase();
    const matches = readIndex().skills.filter((skill) => `${skill.name}\n${skill.description}`.toLowerCase().includes(query));
    for (const skill of matches) console.log(`${terminalSafe(skill.name)}\t${terminalSafe(skill.description)}\t${terminalSafe(skill.path)}`);
    if (matches.length === 0) process.exitCode = 1;
  } else {
    printStatus(readIndex());
  }

}
