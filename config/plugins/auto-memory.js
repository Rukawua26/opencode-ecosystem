import { readFileSync, writeFileSync, existsSync, mkdirSync, appendFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tool } from "@opencode-ai/plugin";

const __dirname = dirname(fileURLToPath(import.meta.url));
const HOME = process.env.HOME || process.env.USERPROFILE || "/tmp";
const DATA_DIR = join(HOME, ".local/share/opencode/plugins-data");
const AUTO_MEMORY_LOG = join(DATA_DIR, "auto-memory.log");
const AUTO_MEMORY_STATE = join(DATA_DIR, "auto-memory-state.json");

const DECISION_PATTERNS = [
  /decidimos\s+(usar|implementar|elegir|optar por)\s+([^\s,]+)/i,
  /decisión:\s*(.+?)(?:\n|$)/i,
  /se eligió\s+([^\s,]+)/i,
  /usaremos\s+([^\s,]+)/i,
  /arquitectura:\s*(.+?)(?:\n|$)/i,
  /razón:\s*(.+?)(?:\n|$)/i,
  /porque\s+(.+?)(?:\n|$)/i,
  /decidimos\s+no\s+usar/i,
  /cambio de diseño/i,
  /refactor/i,
];

const BUG_PATTERNS = [
  /bug\s+(?:en\s+)?([^\s:]+)/i,
  /error\s+(?:en\s+)?([^\s:]+)/i,
  /fix\s+(?:del\s+)?([^\s]+)/i,
  /arregl[ao]\s+(?:el\s+)?bug/i,
  /solucion/i,
  /problema\s+(?:resolviendo|en)/i,
  /stack trace/i,
  /exception/i,
  /crash/i,
];

const ARCHITECTURE_PATTERNS = [
  /arquitectura\s+del\s+([^\s]+)/i,
  /componente\s+([^\s]+)\s+(?:es|es el)/i,
  /se agregó\s+([^\s]+)/i,
  /interfaz\s+([^\s]+)/i,
  /patron\s+de\s+diseño/i,
];

function ensureDir() {
  if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
}

function logAutoMemory(message) {
  const timestamp = new Date().toISOString();
  appendFileSync(AUTO_MEMORY_LOG, `[${timestamp}] ${message}\n`);
}

function extractDecision(text) {
  for (const pattern of DECISION_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      return {
        title: match[1] || "Decisión técnica",
        content: text.slice(0, 500),
        rationale: text.slice(0, 200),
        tags: extractTags(text),
      };
    }
  }
  return null;
}

function extractBug(text) {
  for (const pattern of BUG_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      return {
        title: match[1] || "Bug encontrado",
        description: text.slice(0, 500),
        fix: "Pendiente de implementación",
        lesson: "Pendiente de lección",
        tags: extractTags(text),
      };
    }
  }
  return null;
}

function extractArchitecture(text) {
  for (const pattern of ARCHITECTURE_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      return {
        component: match[1] || "Componente",
        description: text.slice(0, 500),
        rationale: text.slice(0, 200),
        tags: extractTags(text),
      };
    }
  }
  return null;
}

function extractTags(text) {
  const tagPattern = /#\w+|@(w|cli|api|db|ui|backend|frontend|security)/g;
  const matches = text.match(tagPattern) || [];
  return [...new Set(matches)].slice(0, 5).join(",");
}

function getState() {
  if (existsSync(AUTO_MEMORY_STATE)) {
    try {
      return JSON.parse(readFileSync(AUTO_MEMORY_STATE, "utf-8"));
    } catch {
      return { lastDecision: null, lastBug: null };
    }
  }
  return { lastDecision: null, lastBug: null };
}

function setState(state) {
  writeFileSync(AUTO_MEMORY_STATE, JSON.stringify(state, null, 2));
}

export const autoMemoryPlugin = async () => {
  return {
    name: "auto-memory",
    tools: [
      tool({
        name: "auto_memory_save",
        description: "Auto-guardar decisiones, bugs o arquitectura detectados en la conversación. Llama internamente a memory-adapter.",
        parameters: {
          type: "object",
          properties: {
            type: { type: "string", enum: ["decision", "bug", "architecture"], description: "Tipo de información a guardar" },
            content: { type: "string", description: "Texto a analizar y extraer información" },
            project: { type: "string", description: "Nombre del proyecto" },
            projectPath: { type: "string", description: "Ruta del proyecto" },
          },
          required: ["type", "content", "project", "projectPath"],
        },
        execute: async (args) => {
          ensureDir();

          const { type, content, project, projectPath } = args;
          let result = null;

          if (type === "decision") {
            result = extractDecision(content);
            if (result) {
              logAutoMemory(`Decision detected: ${result.title}`);
            }
          } else if (type === "bug") {
            result = extractBug(content);
            if (result) {
              logAutoMemory(`Bug detected: ${result.title}`);
            }
          } else if (type === "architecture") {
            result = extractArchitecture(content);
            if (result) {
              logAutoMemory(`Architecture detected: ${result.component}`);
            }
          }

          return { content: JSON.stringify({ detected: !!result, extracted: result, timestamp: new Date().toISOString() }) };
        },
      }),
      tool({
        name: "auto_memory_summary",
        description: "Obtener resumen de decisiones y bugs detectados en esta sesión",
        parameters: {
          type: "object",
          properties: {
            project: { type: "string" },
            projectPath: { type: "string" },
          },
          required: ["project", "projectPath"],
        },
        execute: async (args) => {
          const state = getState();
          return { content: JSON.stringify(state) };
        },
      }),
    ],
  };
};