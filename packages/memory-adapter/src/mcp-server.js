import { createInterface } from "node:readline";
import { MemoryAdapter } from "./adapter.js";

const adapter = new MemoryAdapter();
adapter.init();

const TOOLS = [
  {
    name: "save_decision",
    description: "Save an architectural or technical decision to persistent memory. Use when a decision is made during a session.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string", description: "Project name" },
        projectPath: { type: "string", description: "Project path" },
        category: { type: "string", description: "Decision category (general, architecture, tech-choice)", default: "general" },
        title: { type: "string", description: "Short title of the decision" },
        content: { type: "string", description: "Decision details" },
        rationale: { type: "string", description: "Why this decision was made" },
        tags: { type: "string", description: "Comma-separated tags for searchability" },
        isPrivate: { type: "boolean", description: "If true, content may contain secrets and should not be shared", default: false },
      },
      required: ["project", "projectPath", "title", "content"],
    },
  },
  {
    name: "save_bug_fix",
    description: "Save a bug and its fix to persistent memory so the AI can learn from past solutions.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
        title: { type: "string", description: "Bug title" },
        description: { type: "string", description: "What was the bug" },
        rootCause: { type: "string", description: "Root cause analysis" },
        fix: { type: "string", description: "How it was fixed" },
        lesson: { type: "string", description: "What we learned" },
        tags: { type: "string" },
      },
      required: ["project", "projectPath", "title", "description", "fix"],
    },
  },
  {
    name: "save_architecture",
    description: "Save architectural component information to persistent memory.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
        component: { type: "string", description: "Component name" },
        description: { type: "string", description: "What this component does" },
        rationale: { type: "string", description: "Why this design" },
        tags: { type: "string" },
      },
      required: ["project", "projectPath", "component", "description"],
    },
  },
  {
    name: "save_preference",
    description: "Save a project or general preference to persistent memory.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
        key: { type: "string", description: "Preference key" },
        value: { type: "string", description: "Preference value" },
      },
      required: ["key", "value"],
    },
  },
  {
    name: "save_session_action",
    description: "Save a session action to the history log. Use when something significant happens during a session.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
        sessionId: { type: "string" },
        action: { type: "string", description: "Action performed" },
        detail: { type: "string", description: "Action details" },
        result: { type: "string", description: "Outcome" },
        filesTouched: { type: "string", description: "Comma-separated files modified" },
      },
      required: ["action"],
    },
  },
  {
    name: "search_memory",
    description: "Search persistent memory for past decisions, bug fixes, and architecture info. Use when you need context from previous sessions.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string", description: "Project name" },
        projectPath: { type: "string", description: "Project path" },
        query: { type: "string", description: "Search query" },
        category: { type: "string", description: "Category filter: decisions, bugs, architecture, or null for all" },
        limit: { type: "number", description: "Max results per category", default: 10 },
      },
      required: ["project", "projectPath"],
    },
  },
  {
    name: "get_context",
    description: "Get recent context for a project: recent decisions, bugs, architecture, and preferences. Use at the start of a session.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
        limit: { type: "number", description: "Max items per category", default: 5 },
      },
      required: ["project", "projectPath"],
    },
  },
  {
    name: "get_history",
    description: "Get session history for a project. Shows what was done, when, and results.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
        limit: { type: "number", description: "Max history entries", default: 20 },
      },
      required: ["project", "projectPath"],
    },
  },
  {
    name: "export_project",
    description: "Export all memory data for a project. Used for syncing/sharing memory between team members.",
    inputSchema: {
      type: "object",
      properties: {
        project: { type: "string" },
        projectPath: { type: "string" },
      },
      required: ["project", "projectPath"],
    },
  },
];

async function handleToolCall(name, args) {
  try {
    switch (name) {
      case "save_decision":
        return { content: [{ type: "text", text: JSON.stringify(adapter.saveDecision(args)) }] };
      case "save_bug_fix":
        return { content: [{ type: "text", text: JSON.stringify(adapter.saveBugFix(args)) }] };
      case "save_architecture":
        return { content: [{ type: "text", text: JSON.stringify(adapter.saveArchitecture(args)) }] };
      case "save_preference":
        return { content: [{ type: "text", text: JSON.stringify(adapter.savePreference(args)) }] };
      case "save_session_action":
        return { content: [{ type: "text", text: JSON.stringify(adapter.saveSessionAction(args)) }] };
      case "search_memory":
        return { content: [{ type: "text", text: JSON.stringify(adapter.searchMemory(args)) }] };
      case "get_context":
        return { content: [{ type: "text", text: JSON.stringify(adapter.getContext(args)) }] };
      case "get_history":
        return { content: [{ type: "text", text: JSON.stringify(adapter.getHistory(args)) }] };
      case "export_project":
        return { content: [{ type: "text", text: JSON.stringify(adapter.exportProject(args)) }] };
      default:
        return { isError: true, content: [{ type: "text", text: `Unknown tool: ${name}` }] };
    }
  } catch (err) {
    return { isError: true, content: [{ type: "text", text: `Error: ${err.message}` }] };
  }
}

function sendMessage(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

async function main() {
  const rl = createInterface({ input: process.stdin });

  rl.on("line", async (line) => {
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      return sendMessage({ jsonrpc: "2.0", error: { code: -32700, message: "Parse error" } });
    }

    const { id, method, params } = msg;

    if (method === "initialize") {
      return sendMessage({
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion: "2024-11-05",
          serverInfo: { name: "memory-adapter", version: "1.0.0" },
          capabilities: { tools: { listChanged: false } },
        },
      });
    }

    if (method === "initialized" || method === "notifications/initialized") return;

    if (method === "tools/list") {
      return sendMessage({ jsonrpc: "2.0", id, result: { tools: TOOLS } });
    }

    if (method === "tools/call") {
      const result = await handleToolCall(params.name, params.arguments || {});
      return sendMessage({ jsonrpc: "2.0", id, result });
    }

    if (method === "ping") {
      return sendMessage({ jsonrpc: "2.0", id, result: {} });
    }

    return sendMessage({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } });
  });

  rl.on("close", () => {
    adapter.close();
    process.exit(0);
  });
}

main();
