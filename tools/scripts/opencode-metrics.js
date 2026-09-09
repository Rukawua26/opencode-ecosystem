#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const invokedDirectly = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (!invokedDirectly) {
  // Este archivo vive en ~/.config/opencode/tools/, que OpenCode importa como
  // módulo de herramientas en el arranque. Importado no debe ejecutar CLI ni salir.
} else {
  main();
}

function main() {

  const HOME = process.env.HOME || process.env.USERPROFILE || "/tmp";
  const file = join(HOME, ".local", "share", "opencode", "plugins-data", "session-metrics.jsonl");
  const days = Math.max(1, Number(process.argv[2] || 7));
  const cutoff = Date.now() - days * 86400000;

  if (!existsSync(file)) {
    console.log("No session metrics recorded yet.");
    process.exit(0);
  }

  const records = readFileSync(file, "utf8")
    .split("\n")
    .filter(Boolean)
    .flatMap((line) => {
      try {
        return [JSON.parse(line)];
      } catch {
        return [];
      }
    })
    .filter((item) => Date.parse(item.timestamp) >= cutoff);

  const summary = {
    days,
    messages: records.length,
    sessions: new Set(records.map((item) => item.session)).size,
    cost: 0,
    input_tokens: 0,
    output_tokens: 0,
    reasoning_tokens: 0,
    cache_read_tokens: 0,
    tools: 0,
    delegations: 0,
    compactions: 0,
    broad_reads: 0,
    verified_messages: 0,
    loop_detected_messages: 0,
    failures: 0,
    models: {},
  };

  for (const item of records) {
    summary.cost += item.cost || 0;
    summary.input_tokens += item.tokens?.input || 0;
    summary.output_tokens += item.tokens?.output || 0;
    summary.reasoning_tokens += item.tokens?.reasoning || 0;
    summary.cache_read_tokens += item.tokens?.cache_read || 0;
    summary.tools += item.tools || 0;
    summary.delegations += item.delegations || 0;
    summary.compactions += item.compactions || 0;
    summary.broad_reads += item.reads_broad || 0;
    summary.verified_messages += item.verified ? 1 : 0;
    summary.loop_detected_messages += item.loop_detected ? 1 : 0;
    summary.failures += item.failed ? 1 : 0;
    const key = `${item.provider}/${item.model}`;
    summary.models[key] ||= { messages: 0, cost: 0, input_tokens: 0, output_tokens: 0 };
    summary.models[key].messages++;
    summary.models[key].cost += item.cost || 0;
    summary.models[key].input_tokens += item.tokens?.input || 0;
    summary.models[key].output_tokens += item.tokens?.output || 0;
  }

  console.log(JSON.stringify(summary, null, 2));

}
