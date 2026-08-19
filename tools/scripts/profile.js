#!/usr/bin/env node

import { join } from "node:path";
import { inspectConfiguration } from "./config-inspect.js";

const args = process.argv.slice(2);
const validateIndex = args.indexOf("--validate");
const validating = validateIndex !== -1;
const validateProfile = validating ? args[validateIndex + 1] : null;
const known = new Set(["--status", "--json", "--help", "-h", "--validate", validateProfile]);
const unknown = args.filter((arg) => !known.has(arg));
if (unknown.length > 0) {
  console.error(`Unknown option: ${unknown[0]}`);
  process.exit(2);
}
if (args.includes("--help") || args.includes("-h")) {
  console.log("Usage: opencode-profile [--status|--json]");
  process.exit(0);
}
if (validating && (!validateProfile || validateProfile.startsWith("--") || args.length !== 2)) {
  console.error("Usage: profile.js --validate <work|personal|light|default>");
  process.exit(2);
}

const jsonMode = args.includes("--json");
const HOME = process.env.HOME || process.env.USERPROFILE || "/tmp";
const OPENCODE_DIR = join(HOME, ".config", "opencode");
const report = inspectConfiguration({ home: HOME, opencodeDir: OPENCODE_DIR });
const { active, activeConfig, main, profiles, notes } = report;

if (validating) {
  const target = validateProfile === "default" ? main : profiles.find((profile) => profile.name === validateProfile);
  if (!target) {
    console.error(`Profile not found: ${validateProfile}`);
    process.exit(1);
  }
  if (!target.valid) {
    console.error(`Invalid profile ${validateProfile}: ${target.error}`);
    process.exit(1);
  }
  process.exit(0);
}

const output = {
  schemaVersion: 1,
  active,
  main,
  profiles,
  notes,
};

if (jsonMode) {
  console.log(JSON.stringify(output, null, 2));
} else {
  console.log("=== OpenCode Profile ===");
  console.log(`Active: ${active.profile}${active.via !== "none" ? ` (via ${active.via})` : ""}`);
  console.log(`Config: ${active.configPath}`);
  console.log(`Model: ${activeConfig?.model || "default"}`);
  console.log(`Small model: ${activeConfig?.smallModel || "default"}`);
  console.log("--- Available profiles ---");
  if (profiles.length === 0) {
    console.log("(none)");
  } else {
    for (const profile of profiles) {
      const marker = profile.name === active.profile ? "*" : " ";
      console.log(`${marker} ${profile.name}${profile.valid ? ` (model: ${profile.model || "default"})` : " (INVALID)"}`);
    }
  }
  if (notes.length > 0) {
    console.log("--- Notes ---");
    for (const note of notes) console.log(`- ${note}`);
  }
}

process.exitCode = 0;
