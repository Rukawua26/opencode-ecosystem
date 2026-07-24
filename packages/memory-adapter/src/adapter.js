import Database from "node:sqlite";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCHEMA_PATH = join(__dirname, "schema.sql");

const DEFAULT_DB_PATH = join(
  process.env.HOME || process.env.USERPROFILE || "/tmp",
  ".local/share/opencode/memory-adapter/memory.db"
);

export class MemoryAdapter {
  constructor(dbPath = DEFAULT_DB_PATH) {
    this.dbPath = dbPath;
    this.db = null;
  }

  init() {
    const dir = dirname(this.dbPath);
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

    this.db = new Database(this.dbPath);
    this.db.exec("PRAGMA journal_mode = WAL;");
    this.db.exec("PRAGMA foreign_keys = ON;");

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
    const existing = this.db.prepare(
      "SELECT id FROM projects WHERE name = ?"
    ).get(name);
    if (existing) return existing.id;

    const result = this.db.prepare(
      "INSERT INTO projects (name, path) VALUES (?, ?)"
    ).run(name, path);
    return result.lastInsertRowid;
  }

  saveDecision({ project, projectPath, category = "general", title, content, rationale, tags, isPrivate = false }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const result = this.db.prepare(
      `INSERT INTO decisions (project_id, category, title, content, rationale, tags, is_private)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(projectId, category, title, content, rationale || null, tags || null, isPrivate ? 1 : 0);
    return { id: result.lastInsertRowid, saved: true };
  }

  saveBugFix({ project, projectPath, title, description, rootCause, fix, lesson, tags }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const result = this.db.prepare(
      `INSERT INTO bug_fixes (project_id, title, description, root_cause, fix, lesson, tags)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(projectId, title, description, rootCause || null, fix, lesson || null, tags || null);
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
    this.db.prepare(
      "DELETE FROM preferences WHERE project_id IS ? AND key = ?"
    ).run(projectId, key);
    const result = this.db.prepare(
      "INSERT INTO preferences (project_id, key, value) VALUES (?, ?, ?)"
    ).run(projectId, key, value);
    return { id: result.lastInsertRowid, saved: true };
  }

  saveSessionAction({ project, projectPath, sessionId, action, detail, result, filesTouched }) {
    const projectId = project ? this.getOrCreateProject(project, projectPath) : null;
    const res = this.db.prepare(
      `INSERT INTO session_history (project_id, session_id, action, detail, result, files_touched)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).run(projectId, sessionId || null, action, detail || null, result || null, filesTouched || null);
    return { id: res.lastInsertRowid, saved: true };
  }

  searchMemory({ project, query, category, limit = 10 }) {
    const projectId = project ? this.getOrCreateProject(project, "") : null;
    const results = {};
    const likeQuery = `%${query || ""}%`;

    if (!category || category === "decisions") {
      results.decisions = this.db.prepare(
        `SELECT id, category, title, content, rationale, tags, created_at
         FROM decisions WHERE project_id = ? AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
         ORDER BY created_at DESC LIMIT ?`
      ).all(projectId, likeQuery, likeQuery, likeQuery, limit);
    }

    if (!category || category === "bugs") {
      results.bugs = this.db.prepare(
        `SELECT id, title, description, root_cause, fix, lesson, tags, created_at
         FROM bug_fixes WHERE project_id = ? AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)
         ORDER BY created_at DESC LIMIT ?`
      ).all(projectId, likeQuery, likeQuery, likeQuery, limit);
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
    const projectId = this.getOrCreateProject(project, projectPath);
    const context = {};

    context.recentDecisions = this.db.prepare(
      "SELECT id, category, title, content, created_at FROM decisions WHERE project_id = ? ORDER BY created_at DESC LIMIT ?"
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

    return context;
  }

  getHistory({ project, projectPath, limit = 20 }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    return this.db.prepare(
      "SELECT id, session_id, action, detail, result, files_touched, created_at FROM session_history WHERE project_id = ? ORDER BY created_at DESC LIMIT ?"
    ).all(projectId, limit);
  }

  exportProject({ project, projectPath }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    return {
      project: this.db.prepare("SELECT * FROM projects WHERE id = ?").get(projectId),
      decisions: this.db.prepare("SELECT * FROM decisions WHERE project_id = ?").all(projectId),
      bugFixes: this.db.prepare("SELECT * FROM bug_fixes WHERE project_id = ?").all(projectId),
      architecture: this.db.prepare("SELECT * FROM architecture WHERE project_id = ?").all(projectId),
      preferences: this.db.prepare("SELECT * FROM preferences WHERE project_id = ?").all(projectId),
      history: this.db.prepare("SELECT * FROM session_history WHERE project_id = ?").all(projectId),
    };
  }
}
