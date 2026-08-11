import { DatabaseSync } from "node:sqlite";
import { chmodSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  parseEventJsonl,
  serializeEventJsonl,
  toMemoryEvent,
  validateMemoryEvent,
} from "./memory-events.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCHEMA_PATH = join(__dirname, "schema.sql");

const DEFAULT_DB_PATH = join(
  process.env.HOME || process.env.USERPROFILE || "/tmp",
  ".local/share/opencode/memory-adapter/memory.db"
);

let ollamaAvailable = null;

function checkOllama() {
  if (ollamaAvailable !== null) return ollamaAvailable;
  try {
    execFileSync("ollama", ["embed", "--help"], { stdio: "pipe", timeout: 2000 });
    ollamaAvailable = true;
    return true;
  } catch {
    ollamaAvailable = false;
    return false;
  }
}

const EVENT_SOURCES = {
  decision: {
    table: "decisions",
    columns: "id, category, title, content, rationale, tags, is_private, COALESCE(created_at, '1970-01-01 00:00:00') AS created_at",
  },
  bugfix: {
    table: "bug_fixes",
    columns: "id, title, description, root_cause, fix, lesson, tags, COALESCE(created_at, '1970-01-01 00:00:00') AS created_at",
  },
  architecture: {
    table: "architecture",
    columns: "id, component, description, rationale, tags, COALESCE(created_at, '1970-01-01 00:00:00') AS created_at",
  },
  preference: {
    table: "preferences",
    columns: "id, key, value, COALESCE(created_at, '1970-01-01 00:00:00') AS created_at",
  },
  operational: {
    table: "session_history",
    columns: "id, session_id, action, detail, result, files_touched, COALESCE(created_at, '1970-01-01 00:00:00') AS created_at",
  },
};

function eventTimestamp(value, name) {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value !== "string") throw new Error(`invalid: ${name} must be a valid date`);
  const calendar = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|[+-]\d{2}:\d{2})?)?$/.exec(value);
  if (!calendar) throw new Error(`invalid: ${name} must be a valid date`);
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, fraction, zone] = calendar;
  const [year, month, day] = [yearText, monthText, dayText].map(Number);
  const calendarDate = new Date(Date.UTC(year, month - 1, day));
  if (calendarDate.getUTCFullYear() !== year
    || calendarDate.getUTCMonth() !== month - 1
    || calendarDate.getUTCDate() !== day) {
    throw new Error(`invalid: ${name} must be a valid date`);
  }

  if (hourText === undefined) {
    return `${yearText}-${monthText}-${dayText} ${name === "until" ? "23:59:59" : "00:00:00"}`;
  }
  const [hour, minute, second] = [hourText, minuteText, secondText].map(Number);
  if (hour > 23 || minute > 59 || second > 59) {
    throw new Error(`invalid: ${name} must be a valid date`);
  }
  if (!zone) return `${yearText}-${monthText}-${dayText} ${hourText}:${minuteText}:${secondText}`;

  const timestamp = new Date(
    `${yearText}-${monthText}-${dayText}T${hourText}:${minuteText}:${secondText}${fraction ? `.${fraction}` : ""}${zone}`,
  );
  if (Number.isNaN(timestamp.getTime())) throw new Error(`invalid: ${name} must be a valid date`);
  return timestamp.toISOString().replace("T", " ").replace(/\.\d{3}Z$/, "");
}

function importedTimestamp(value) {
  return eventTimestamp(value, "created_at")
    || new Date().toISOString().replace("T", " ").replace(/\.\d{3}Z$/, "");
}

function eventLimit(value) {
  if (value === undefined) return 50;
  if (!Number.isInteger(value) || value < 1) throw new Error("invalid: limit must be a positive integer");
  return Math.min(value, 1000);
}

function embedQuery(query) {
  if (!checkOllama()) return null;
  try {
    const result = execFileSync("ollama", ["embed", "nomic-embed-text", query], {
      encoding: "utf-8",
      timeout: 10000,
    });
    const parsed = JSON.parse(result);
    return parsed?.embedding || parsed?.embeddings?.[0] || null;
  } catch {
    return null;
  }
}

function cosineSimilarity(left, right) {
  if (!left?.length || left.length !== right?.length) return -1;
  let dot = 0;
  let leftNorm = 0;
  let rightNorm = 0;
  for (let index = 0; index < left.length; index++) {
    dot += left[index] * right[index];
    leftNorm += left[index] ** 2;
    rightNorm += right[index] ** 2;
  }
  return leftNorm && rightNorm ? dot / Math.sqrt(leftNorm * rightNorm) : -1;
}

function rankByEmbedding(rows, queryEmbedding, limit) {
  return rows
    .map(({ embedding, ...row }) => {
      try {
        return { ...row, score: cosineSimilarity(queryEmbedding, JSON.parse(embedding)) };
      } catch {
        return { ...row, score: -1 };
      }
    })
    .filter((row) => row.score >= 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, limit);
}

function validateImportData(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Import data must be an object");
  if (!data.project || typeof data.project.name !== "string" || !data.project.name.trim()) {
    throw new Error("Import project.name is required");
  }
  const arrays = ["decisions", "bugFixes", "architecture", "preferences", "history"];
  for (const key of arrays) {
    if (data[key] !== undefined && !Array.isArray(data[key])) throw new Error(`${key} must be an array`);
    if (data[key]?.length > 10000) throw new Error(`${key} exceeds 10000 records`);
    for (const item of data[key] || []) {
      if (!item || typeof item !== "object" || Array.isArray(item)) throw new Error(`${key} contains an invalid record`);
    }
  }

  const requiredStrings = {
    decisions: ["title", "content"],
    bugFixes: ["title", "description", "fix"],
    architecture: ["component", "description"],
    preferences: ["key", "value"],
    history: ["action"],
  };
  for (const [collection, fields] of Object.entries(requiredStrings)) {
    for (const item of data[collection] || []) {
      for (const field of fields) {
        if (typeof item[field] !== "string" || !item[field].trim()) {
          throw new Error(`${collection}.${field} must be a non-empty string`);
        }
      }
    }
  }
}

export class MemoryAdapter {
  constructor(dbPath = DEFAULT_DB_PATH) {
    this.dbPath = dbPath;
    this.db = null;
    this.useEmbeddings = checkOllama();
  }

  init() {
    const dir = dirname(this.dbPath);
    const createdDirectory = !existsSync(dir);
    if (createdDirectory) mkdirSync(dir, { recursive: true, mode: 0o700 });
    if (createdDirectory && process.platform !== "win32") chmodSync(dir, 0o700);

    this.db = new DatabaseSync(this.dbPath);
    this.db.exec("PRAGMA journal_mode = WAL;");
    this.db.exec("PRAGMA foreign_keys = ON;");
    if (process.platform !== "win32") {
      for (const file of [this.dbPath, `${this.dbPath}-wal`, `${this.dbPath}-shm`]) {
        if (existsSync(file)) chmodSync(file, 0o600);
      }
    }

    const schema = readFileSync(SCHEMA_PATH, "utf-8");
    this.db.exec(schema);

    return this;
  }

  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }

  getOrCreateProject(name, path) {
    const normalizedPath = resolve(path || ".");
    const existing = this.db.prepare("SELECT id, path FROM projects WHERE name = ?").get(name);
    if (existing) {
      if (resolve(existing.path || ".") !== normalizedPath) throw new Error(`Project path mismatch for ${name}`);
      return existing.id;
    }

    const result = this.db.prepare("INSERT INTO projects (name, path) VALUES (?, ?)").run(name, normalizedPath);
    return result.lastInsertRowid;
  }

  findProject(name, path) {
    const existing = this.db.prepare("SELECT id, path FROM projects WHERE name = ?").get(name);
    if (!existing || resolve(existing.path || ".") !== resolve(path || ".")) return null;
    return existing.id;
  }

  saveDecision({ project, projectPath, category = "general", title, content, rationale, tags, isPrivate = false }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const result = this.db.prepare(
      `INSERT INTO decisions (project_id, category, title, content, rationale, tags, is_private)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(projectId, category, title, content, rationale || null, tags || null, isPrivate ? 1 : 0);

    if (this.useEmbeddings) {
      const embedding = embedQuery(`${title} ${content} ${rationale || ""} ${tags || ""}`);
      if (embedding) {
        this.db.prepare("INSERT INTO decision_embeddings (decision_id, embedding) VALUES (?, ?)")
          .run(result.lastInsertRowid, JSON.stringify(embedding));
      }
    }

    return { id: result.lastInsertRowid, saved: true };
  }

  saveBugFix({ project, projectPath, title, description, rootCause, fix, lesson, tags }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const result = this.db.prepare(
      `INSERT INTO bug_fixes (project_id, title, description, root_cause, fix, lesson, tags)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(projectId, title, description, rootCause || null, fix, lesson || null, tags || null);

    if (this.useEmbeddings) {
      const embedding = embedQuery(`${title} ${description || ""} ${rootCause || ""} ${fix || ""} ${lesson || ""} ${tags || ""}`);
      if (embedding) {
        this.db.prepare("INSERT INTO bug_embedding_cache (bug_id, embedding) VALUES (?, ?)")
          .run(result.lastInsertRowid, JSON.stringify(embedding));
      }
    }

    return { id: result.lastInsertRowid, saved: true };
  }

  saveArchitecture({ project, projectPath, component, description, rationale, tags }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const result = this.db.prepare(
      `INSERT INTO architecture (project_id, component, description, rationale, tags)
       VALUES (?, ?, ?, ?, ?)`
    ).run(projectId, component, description, rationale || null, tags || null);
    return { id: result.lastInsertRowid, saved: true };
  }

  savePreference({ project, projectPath, key, value }) {
    const projectId = project ? this.getOrCreateProject(project, projectPath) : null;
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const existing = this.db.prepare(
        "SELECT id FROM preferences WHERE project_id IS ? AND key = ? ORDER BY id DESC LIMIT 1",
      ).get(projectId, key);
      let id;
      if (existing) {
        this.db.prepare("DELETE FROM preferences WHERE project_id IS ? AND key = ? AND id <> ?")
          .run(projectId, key, existing.id);
        this.db.prepare("UPDATE preferences SET value = ? WHERE id = ?").run(value, existing.id);
        id = existing.id;
      } else {
        id = this.db.prepare("INSERT INTO preferences (project_id, key, value) VALUES (?, ?, ?)")
          .run(projectId, key, value).lastInsertRowid;
      }
      this.db.exec("COMMIT");
      return { id, saved: true };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  saveSessionAction({ project, projectPath, sessionId, action, detail, result, filesTouched }) {
    const projectId = project ? this.getOrCreateProject(project, projectPath) : null;
    const res = this.db.prepare(
      `INSERT INTO session_history (project_id, session_id, action, detail, result, files_touched)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).run(projectId, sessionId || null, action, detail || null, result || null, filesTouched || null);
    return { id: res.lastInsertRowid, saved: true };
  }

  searchMemory({ project, projectPath, query, category, limit = 10, semantic = true }) {
    const projectId = project ? this.findProject(project, projectPath) : null;
    const results = {};
    const likeQuery = `%${query || ""}%`;

    if (!projectId) {
      if (!category || category === "decisions") results.decisions = [];
      if (!category || category === "bugs") results.bugs = [];
      if (!category || category === "architecture") results.architecture = [];
      return results;
    }

    const queryEmbedding = semantic && this.useEmbeddings && query ? embedQuery(query) : null;

    if (!category || category === "decisions") {
      if (queryEmbedding) {
        const rows = this.db.prepare(
            `SELECT d.id, d.category, d.title, d.content, d.rationale, d.tags, d.created_at,
                     de.embedding
             FROM decisions d
             LEFT JOIN decision_embeddings de ON d.id = de.decision_id
             WHERE d.project_id = ? AND d.is_private = 0`
          ).all(projectId);
        const withEmbeddings = rows.filter((row) => row.embedding);
        const ranked = rankByEmbedding(withEmbeddings, queryEmbedding, limit);
        const withoutEmbeddings = rows.filter((row) => !row.embedding);
        if (withoutEmbeddings.length > 0 && likeQuery.trim()) {
          const textual = withoutEmbeddings.filter((row) =>
            (row.title || "").includes(likeQuery.slice(1, -1)) ||
            (row.content || "").includes(likeQuery.slice(1, -1)) ||
            (row.tags || "").includes(likeQuery.slice(1, -1))
          );
          results.decisions = [...ranked, ...textual].slice(0, limit);
        } else {
          results.decisions = ranked;
        }
      } else {
        results.decisions = this.db.prepare(
          `SELECT id, category, title, content, rationale, tags, created_at
           FROM decisions WHERE project_id = ? AND is_private = 0 AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
           ORDER BY created_at DESC LIMIT ?`
        ).all(projectId, likeQuery, likeQuery, likeQuery, limit);
      }
    }

    if (!category || category === "bugs") {
      if (queryEmbedding) {
        const rows = this.db.prepare(
            `SELECT b.id, b.title, b.description, b.root_cause, b.fix, b.lesson, b.tags, b.created_at,
                     be.embedding
             FROM bug_fixes b
             LEFT JOIN bug_embedding_cache be ON b.id = be.bug_id
             WHERE b.project_id = ?`
          ).all(projectId);
        const withEmbeddings = rows.filter((row) => row.embedding);
        const ranked = rankByEmbedding(withEmbeddings, queryEmbedding, limit);
        const withoutEmbeddings = rows.filter((row) => !row.embedding);
        if (withoutEmbeddings.length > 0 && (likeQuery || "").trim()) {
          const textual = withoutEmbeddings.filter((row) =>
            (row.title || "").includes(likeQuery.slice(1, -1)) ||
            (row.description || "").includes(likeQuery.slice(1, -1)) ||
            (row.tags || "").includes(likeQuery.slice(1, -1))
          );
          results.bugs = [...ranked, ...textual].slice(0, limit);
        } else {
          results.bugs = ranked;
        }
      } else {
        results.bugs = this.db.prepare(
          `SELECT id, title, description, root_cause, fix, lesson, tags, created_at
           FROM bug_fixes WHERE project_id = ? AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)
           ORDER BY created_at DESC LIMIT ?`
        ).all(projectId, likeQuery, likeQuery, likeQuery, limit);
      }
    }

    if (!category || category === "architecture") {
      results.architecture = this.db.prepare(
        `SELECT id, component, description, rationale, tags, created_at
         FROM architecture WHERE project_id = ? AND (component LIKE ? OR description LIKE ? OR tags LIKE ?)
         ORDER BY created_at DESC LIMIT ?`
      ).all(projectId, likeQuery, likeQuery, likeQuery, limit);
    }

    return results;
  }

  getContext({ project, projectPath, limit = 5 }) {
    const projectId = this.findProject(project, projectPath);
    const context = {};

    if (!projectId) {
      return { recentDecisions: [], recentBugs: [], architecture: [], preferences: [], ollamaAvailable: this.useEmbeddings };
    }

    context.recentDecisions = this.db.prepare(
      "SELECT id, category, title, content, created_at FROM decisions WHERE project_id = ? AND is_private = 0 ORDER BY created_at DESC LIMIT ?"
    ).all(projectId, limit);

    context.recentBugs = this.db.prepare(
      "SELECT id, title, fix, lesson, created_at FROM bug_fixes WHERE project_id = ? ORDER BY created_at DESC LIMIT ?"
    ).all(projectId, limit);

    context.architecture = this.db.prepare(
      "SELECT id, component, description, created_at FROM architecture WHERE project_id = ? ORDER BY created_at DESC LIMIT ?"
    ).all(projectId, limit);

    context.preferences = this.db.prepare(
      "SELECT key, value FROM preferences WHERE project_id = ?"
    ).all(projectId);

    context.ollamaAvailable = this.useEmbeddings;

    return context;
  }

  getHistory({ project, projectPath, limit = 20 }) {
    const projectId = this.findProject(project, projectPath);
    if (!projectId) return [];
    return this.db.prepare(
      "SELECT id, session_id, action, detail, result, files_touched, created_at FROM session_history WHERE project_id = ? ORDER BY created_at DESC LIMIT ?"
    ).all(projectId, limit);
  }

  listEvents({
    project,
    projectPath,
    kind,
    since,
    until,
    limit,
    includePrivate = false,
    references,
  }) {
    const projectId = this.findProject(project, projectPath);
    if (!projectId) return [];

    const kinds = kind === undefined ? Object.keys(EVENT_SOURCES) : (Array.isArray(kind) ? kind : [kind]);
    for (const eventKind of kinds) {
      if (!EVENT_SOURCES[eventKind]) throw new Error(`invalid: unsupported event kind ${eventKind}`);
    }

    const normalizedSince = eventTimestamp(since, "since");
    const normalizedUntil = eventTimestamp(until, "until");
    if (normalizedSince && normalizedUntil && normalizedSince > normalizedUntil) {
      throw new Error("invalid: since must be before until");
    }
    const normalizedLimit = eventLimit(limit);

    const events = [];
    for (const eventKind of kinds) {
      const source = EVENT_SOURCES[eventKind];
      const conditions = ["project_id = ?"];
      const params = [projectId];
      if (eventKind === "decision" && !includePrivate) conditions.push("is_private = 0");
      if (normalizedSince) {
        conditions.push("created_at >= ?");
        params.push(normalizedSince);
      }
      if (normalizedUntil) {
        conditions.push("created_at <= ?");
        params.push(normalizedUntil);
      }
      params.push(normalizedLimit);

      const rows = this.db.prepare(
        `SELECT ${source.columns} FROM ${source.table}
         WHERE ${conditions.join(" AND ")}
         ORDER BY created_at DESC, id DESC LIMIT ?`,
      ).all(...params);
      events.push(...rows.map((row) => toMemoryEvent(row, eventKind, project, references)));
    }

    return events
      .sort((left, right) => right.created_at.localeCompare(left.created_at)
        || right.event_id.localeCompare(left.event_id))
      .slice(0, normalizedLimit);
  }

  listChangedEvents({
    project,
    projectPath,
    kind,
    since,
    until,
    limit,
    includePrivate = false,
    references,
    knownEvents = [],
  }) {
    if (!Array.isArray(knownEvents)) throw new Error("invalid: knownEvents must be an array");
    if (knownEvents.length > 10000) {
      throw new Error("invalid: event state exceeds 10000 events; rotate or replace the --state file");
    }
    const knownHashes = new Map(knownEvents.map((event) => {
      const validated = validateMemoryEvent(event);
      return [validated.event_id, validated.content_hash];
    }));
    const projectId = this.findProject(project, projectPath);
    if (!projectId) return [];

    const kinds = kind === undefined ? Object.keys(EVENT_SOURCES) : (Array.isArray(kind) ? kind : [kind]);
    for (const eventKind of kinds) {
      if (!EVENT_SOURCES[eventKind]) throw new Error(`invalid: unsupported event kind ${eventKind}`);
    }
    const normalizedSince = eventTimestamp(since, "since");
    const normalizedUntil = eventTimestamp(until, "until");
    if (normalizedSince && normalizedUntil && normalizedSince > normalizedUntil) {
      throw new Error("invalid: since must be before until");
    }
    const normalizedLimit = eventLimit(limit);

    const events = [];
    for (const eventKind of kinds) {
      const source = EVENT_SOURCES[eventKind];
      const conditions = ["project_id = ?"];
      const params = [projectId];
      if (eventKind === "decision" && !includePrivate) conditions.push("is_private = 0");
      if (normalizedSince) {
        conditions.push("created_at >= ?");
        params.push(normalizedSince);
      }
      if (normalizedUntil) {
        conditions.push("created_at <= ?");
        params.push(normalizedUntil);
      }

      const rows = this.db.prepare(
        `SELECT ${source.columns} FROM ${source.table}
         WHERE ${conditions.join(" AND ")}
         ORDER BY created_at DESC, id DESC`,
      ).iterate(...params);
      let changedForKind = 0;
      for (const row of rows) {
        const event = toMemoryEvent(row, eventKind, project, references);
        if (knownHashes.get(event.event_id) === event.content_hash) continue;
        events.push(event);
        changedForKind += 1;
        if (changedForKind >= normalizedLimit) break;
      }
    }

    return events
      .sort((left, right) => right.created_at.localeCompare(left.created_at)
        || right.event_id.localeCompare(left.event_id))
      .slice(0, normalizedLimit);
  }

  exportEventsJsonl(options) {
    const events = options.knownEvents === undefined
      ? this.listEvents(options)
      : this.listChangedEvents(options);
    return serializeEventJsonl(events);
  }

  validateEventsJsonl(jsonl) {
    return parseEventJsonl(jsonl);
  }

  exportProject({ project, projectPath, includePrivate = false, includeOperational = false }) {
    const projectId = this.findProject(project, projectPath);
    if (!projectId) {
      return {
        project: { name: project, path: resolve(projectPath || ".") },
        decisions: [],
        bugFixes: [],
        architecture: [],
        preferences: [],
        history: [],
        ollamaAvailable: this.useEmbeddings,
      };
    }
    return {
      project: this.db.prepare("SELECT * FROM projects WHERE id = ?").get(projectId),
      decisions: includePrivate
        ? this.db.prepare("SELECT * FROM decisions WHERE project_id = ?").all(projectId)
        : this.db.prepare("SELECT * FROM decisions WHERE project_id = ? AND is_private = 0").all(projectId),
      bugFixes: includeOperational
        ? this.db.prepare("SELECT * FROM bug_fixes WHERE project_id = ?").all(projectId)
        : [],
      architecture: includeOperational
        ? this.db.prepare("SELECT * FROM architecture WHERE project_id = ?").all(projectId)
        : [],
      preferences: includeOperational
        ? this.db.prepare("SELECT * FROM preferences WHERE project_id = ?").all(projectId)
        : [],
      history: includeOperational
        ? this.db.prepare("SELECT * FROM session_history WHERE project_id = ?").all(projectId)
        : [],
      ollamaAvailable: this.useEmbeddings,
    };
  }

  importProject(data) {
    validateImportData(data);
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const projectId = this.getOrCreateProject(data.project.name, data.project.path || ".");
      const clearTables = [
        "DELETE FROM decisions WHERE project_id = ?",
        "DELETE FROM bug_fixes WHERE project_id = ?",
        "DELETE FROM architecture WHERE project_id = ?",
        "DELETE FROM preferences WHERE project_id = ?",
        "DELETE FROM session_history WHERE project_id = ?",
      ];
      for (const sql of clearTables) this.db.prepare(sql).run(projectId);

      if (data.decisions) {
        for (const d of data.decisions) {
          this.db.prepare(
            "INSERT INTO decisions (project_id, category, title, content, rationale, tags, is_private, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
          ).run(projectId, d.category || "general", d.title, d.content, d.rationale || null,
            d.tags || null, d.is_private ? 1 : 0, importedTimestamp(d.created_at));
        }
      }
      if (data.bugFixes) {
        for (const b of data.bugFixes) {
          this.db.prepare(
            "INSERT INTO bug_fixes (project_id, title, description, root_cause, fix, lesson, tags, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
          ).run(projectId, b.title, b.description, b.root_cause || null, b.fix, b.lesson || null,
            b.tags || null, importedTimestamp(b.created_at));
        }
      }
      if (data.architecture) {
        for (const a of data.architecture) {
          this.db.prepare(
            "INSERT INTO architecture (project_id, component, description, rationale, tags, created_at) VALUES (?, ?, ?, ?, ?, ?)"
          ).run(projectId, a.component, a.description, a.rationale || null, a.tags || null,
            importedTimestamp(a.created_at));
        }
      }
      if (data.preferences) {
        for (const p of data.preferences) {
          this.db.prepare("INSERT INTO preferences (project_id, key, value, created_at) VALUES (?, ?, ?, ?)")
            .run(projectId, p.key, p.value, importedTimestamp(p.created_at));
        }
      }
      if (data.history) {
        for (const h of data.history) {
          this.db.prepare(
            "INSERT INTO session_history (project_id, session_id, action, detail, result, files_touched, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
          ).run(projectId, h.session_id || null, h.action, h.detail || null, h.result || null,
            h.files_touched || null, importedTimestamp(h.created_at));
        }
      }

      this.db.exec("COMMIT");
      return { imported: true, projectId };
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }

  async exportToObsidian({ project, projectPath, outputDir, includeBugs = false }) {
    const projectId = this.findProject(project, projectPath);
    if (!projectId) return { decisions: 0, bugs: 0, outputDir: outputDir || join(process.cwd(), "docs", "decisions") };
    const decisions = this.db.prepare("SELECT * FROM decisions WHERE project_id = ? AND is_private = 0").all(projectId);
    const bugs = includeBugs
      ? this.db.prepare("SELECT * FROM bug_fixes WHERE project_id = ?").all(projectId)
      : [];

    const fs = await import("node:fs");
    const nodePath = await import("node:path");

    const outDir = outputDir || nodePath.join(process.cwd(), "docs", "decisions");
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    for (const d of decisions) {
      const slug = d.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      const fileName = `${slug}-${d.id}.md`;
      const content = `---
title: "${d.title}"
category: "${d.category}"
tags: [${d.tags || ""}]
created_at: "${d.created_at}"
---

# ${d.title}

${d.content}

## Rationale

${d.rationale || "N/A"}

## Related Decisions

[[Decisiones Anteriores]]
`;
      fs.writeFileSync(nodePath.join(outDir, fileName), content, { mode: 0o600 });
    }

    for (const b of bugs) {
      const slug = b.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      const fileName = `bug-${slug}-${b.id}.md`;
      const content = `---
title: "${b.title}"
tags: [${b.tags || ""}]
created_at: "${b.created_at}"
---

# ${b.title}

## Description

${b.description}

## Root Cause

${b.root_cause || "N/A"}

## Fix

${b.fix}

## Lesson

${b.lesson || "N/A"}
`;
      fs.writeFileSync(nodePath.join(outDir, fileName), content, { mode: 0o600 });
    }

    return { decisions: decisions.length, bugs: bugs.length, outputDir: outDir };
  }
}
