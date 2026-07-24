import { appendFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { metricFromMessage } from "../lib/session-metrics.js";

const HOME = process.env.HOME || "/tmp";
const DATA_DIR = join(HOME, ".local/share/opencode/plugins-data");
const LOG_FILE = join(DATA_DIR, "session-metrics.jsonl");
const sessions = new Map();
const recorded = new Set();

function stateFor(sessionID) {
  if (!sessions.has(sessionID)) sessions.set(sessionID, { tools: 0, delegations: 0, compactions: 0 });
  return sessions.get(sessionID);
}

function appendMetric(metric) {
  try {
    if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true, mode: 0o700 });
    if (!existsSync(LOG_FILE)) writeFileSync(LOG_FILE, "", { mode: 0o600 });
    appendFileSync(LOG_FILE, `${JSON.stringify(metric)}\n`);
  } catch {
    // Metrics must never interrupt the coding session.
  }
}

export const sessionMetricsPlugin = async () => ({
  "tool.execute.before": async (input) => {
    const state = stateFor(input.sessionID);
    state.tools += 1;
    if (input.tool === "task") state.delegations += 1;
  },
  event: async ({ event }) => {
    if (event.type === "session.compacted") {
      stateFor(event.properties.sessionID).compactions += 1;
      return;
    }
    if (event.type === "session.deleted") {
      sessions.delete(event.properties.sessionID);
      return;
    }
    if (event.type !== "message.updated") return;
    const info = event.properties.info;
    if (recorded.has(info.id)) return;
    const metric = metricFromMessage(info, stateFor(event.properties.sessionID));
    if (!metric) return;
    recorded.add(info.id);
    appendMetric(metric);
  },
});

export default sessionMetricsPlugin;
