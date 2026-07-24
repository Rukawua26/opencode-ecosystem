#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, mkdirSync, execSync, readdirSync, statSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { exit } from "node:process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DEFAULT_DB_PATH = join(process.env.HOME || process.env.USERPROFILE || "/tmp", ".local/share/opencode/memory-adapter/memory.db");

const commands = {
  init: {
    description: "Initialize memory adapter database",
    run: (args) => {
      const dbPath = args.db || DEFAULT_DB_PATH;
      const dir = dirname(dbPath);
      if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
      const schema = readFileSync(join(__dirname, "schema.sql"), "utf-8");
      const Database = (await import("node:sqlite")).default;
      const db = new Database(dbPath);
      db.exec(schema);
      db.close();
      console.log(`[OK] Database initialized at ${dbPath}`);
    },
  },
  export: {
    description: "Export project memory to JSON file",
    run: async (args) => {
      if (!args.project) {
        console.error("[ERROR] --project required");
        exit(1);
      }
      const { MemoryAdapter } = await import("./adapter.js");
      const adapter = new MemoryAdapter(args.db);
      adapter.init();
      const data = adapter.exportProject({ project: args.project, projectPath: args.path || process.cwd() });
      const outputPath = args.out || join(process.cwd(), "memory-export.json");
      writeFileSync(outputPath, JSON.stringify(data, null, 2));
      console.log(`[OK] Exported to ${outputPath}`);
      adapter.close();
    },
  },
  import: {
    description: "Import memory from JSON file",
    run: async (args) => {
      if (!args.file) {
        console.error("[ERROR] --file required");
        exit(1);
      }
      const { MemoryAdapter } = await import("./adapter.js");
      const adapter = new MemoryAdapter(args.db);
      adapter.init();
      const data = JSON.parse(readFileSync(args.file, "utf-8"));
      const result = adapter.importProject(data);
      console.log(`[OK] Imported project "${data.project.name}" (${result.projectId})`);
      adapter.close();
    },
  },
  sync: {
    description: "Sync memory with git (export -> git add -> commit)",
    run: async (args) => {
      const { MemoryAdapter } = await import("./adapter.js");
      const adapter = new MemoryAdapter(args.db);
      adapter.init();
      const data = adapter.exportProject({ project: args.project, projectPath: args.path || process.cwd() });
      const outputPath = args.out || join(process.cwd(), "memory-sync.json");
      writeFileSync(outputPath, JSON.stringify(data, null, 2));
      console.log(`[OK] Exported to ${outputPath}`);

      try {
        execSync(`git add ${outputPath}`, { cwd: process.cwd() });
        execSync(`git commit -m "chore: sync memory for ${args.project}"`, { cwd: process.cwd() });
        console.log("[OK] Committed to git");
      } catch (err) {
        console.log("[INFO] No git changes to commit or not a git repo");
      }

      adapter.close();
    },
  },
  status: {
    description: "Show memory adapter status",
    run: async (args) => {
      const { MemoryAdapter } = await import("./adapter.js");
      const adapter = new MemoryAdapter(args.db);
      adapter.init();
      const ctx = adapter.getContext({ project: args.project || "default", projectPath: args.path || process.cwd() });
      console.log(JSON.stringify(ctx, null, 2));
      adapter.close();
    },
  },
};

const args = process.argv.slice(2);
const opts = {};
let cmd = null;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg.startsWith("--")) {
    const key = arg.slice(2);
    const val = args[i + 1];
    if (val && !val.startsWith("--")) {
      opts[key] = val;
      i++;
    } else {
      opts[key] = true;
    }
  } else if (!cmd) {
    cmd = arg;
  }
}

if (!cmd || !commands[cmd]) {
  console.log("Usage: memory-adapter <command> [options]");
  console.log("\nCommands:");
  for (const [name, cmdObj] of Object.entries(commands)) {
    console.log(`  ${name.padEnd(12)} ${cmdObj.description}`);
  }
  console.log("\nOptions:");
  console.log("  --db     Path to database file");
  console.log("  --project Project name");
  console.log("  --path   Project path");
  console.log("  --out    Output file path");
  console.log("  --file   Input file path");
  exit(1);
}

commands[cmd].run({ ...opts, _cmd: cmd }).catch((err) => {
  console.error("[ERROR]", err.message);
  exit(1);
});