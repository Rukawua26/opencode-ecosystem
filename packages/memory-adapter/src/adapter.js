import Database from "node:sqlite";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { execSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

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
    execSync("ollama list", { stdio: "pipe", timeout: 2000 });
    ollamaAvailable = true;
    return true;
  } catch {
    ollamaAvailable = false;
    return false;
  }
}

function embedQuery(query) {
  if (!checkOllama()) return null;
  try {
    const result = execSync(`ollama embed nomic-embed-text "${query.replace(/"/g, '\\"')}"`, {
      encoding: "utf-8",
      timeout: 10000,
    });
    const parsed = JSON.parse(result);
    return parsed?.embedding || null;
  } catch {
    return null;
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
    const existing = this.db.prepare("SELECT id FROM projects WHERE name = ?").get(name);
    if (existing) return existing.id;

    const result = this.db.prepare("INSERT INTO projects (name, path) VALUES (?, ?)").run(name, path);
    return result.lastInsertRowid;
  }

  saveDecision({ project, projectPath, category = "general", title, content, rationale, tags, isPrivate = false }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const result = this.db.prepare(
      `INSERT INTO decisions (project_id, category, title, content, rationale, tags, is_private)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run(projectId, category, title, content, rationale || null, tags || null, isPrivate ? 1 : 0);

    if (this.useEmbeddings) {
      const embedding = embedQuery(title + " " + (rationale || ""));
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
      const embedding = embedQuery(title + " " + (description || "") + " " + (fix || ""));
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
    this.db.prepare("DELETE FROM preferences WHERE project_id IS ? AND key = ?").run(projectId, key);
    const result = this.db.prepare("INSERT INTO preferences (project_id, key, value) VALUES (?, ?, ?)")
      .run(projectId, key, value);
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

  searchMemory({ project, query, category, limit = 10, semantic = true }) {
    const projectId = project ? this.getOrCreateProject(project, "") : null;
    const results = {};
    const likeQuery = `%${query || ""}%`;

    const needSemantic = semantic && this.useEmbeddings && query;

    if (!category || category === "decisions") {
      if (needSemantic) {
        const embedding = embedQuery(query);
        if (embedding) {
          const rows = this.db.prepare(
            `SELECT d.id, d.category, d.title, d.content, d.rationale, d.tags, d.created_at,
                    de.embedding
             FROM decisions d
             LEFT JOIN decision_embeddings de ON d.id = de.decision_id
             WHERE d.project_id = ?
             ORDER BY (CASE WHEN de.embedding IS NOT NULL THEN 1 ELSE 0 END) DESC, d.created_at DESC
             LIMIT ?`
          ).all(projectId, limit);
          results.decisions = rows;
        }
      }
      if (!semantic || !needSemantic) {
        results.decisions = this.db.prepare(
          `SELECT id, category, title, content, rationale, tags, created_at
           FROM decisions WHERE project_id = ? AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
           ORDER BY created_at DESC LIMIT ?`
        ).all(projectId, likeQuery, likeQuery, likeQuery, limit);
      }
    }

    if (!category || category === "bugs") {
      if (needSemantic) {
        const embedding = embedQuery(query);
        if (embedding) {
          const rows = this.db.prepare(
            `SELECT b.id, b.title, b.description, b.root_cause, b.fix, b.lesson, b.tags, b.created_at,
                    be.embedding
             FROM bug_fixes b
             LEFT JOIN bug_embedding_cache be ON b.id = be.bug_id
             WHERE b.project_id = ?
             ORDER BY (CASE WHEN be.embedding IS NOT NULL THEN 1 ELSE 0 END) DESC, b.created_at DESC
             LIMIT ?`
          ).all(projectId, limit);
          results.bugs = rows;
        }
      }
      if (!semantic || !needSemantic) {
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

    context.ollamaAvailable = this.useEmbeddings;

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
      ollamaAvailable: this.useEmbeddings,
    };
  }

  importProject(data) {
    const projectId = this.getOrCreateProject(data.project.name || "imported", data.project.path || "");
    const clearTables = [
      "DELETE FROM decisions WHERE project_id = ?",
      "DELETE FROM bug_fixes WHERE project_id = ?",
      "DELETE FROM architecture WHERE project_id = ?",
      "DELETE FROM preferences WHERE project_id = ?",
      "DELETE FROM session_history WHERE project_id = ?",
      "DELETE FROM decision_embeddings WHERE decision_id NOT IN (SELECT id FROM decisions)",
      "DELETE FROM bug_embedding_cache WHERE bug_id NOT IN (SELECT id FROM bug_fixes)",
    ];
    for (const sql of clearTables) {
      this.db.prepare(sql).run(projectId);
    }

    if (data.decisions) {
      for (const d of data.decisions) {
        this.db.prepare(
          "INSERT INTO decisions (id, project_id, category, title, content, rationale, tags, is_private, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ).run(d.id, projectId, d.category, d.title, d.content, d.rationale, d.tags, d.is_private, d.created_at);
      }
    }
    if (data.bugFixes) {
      for (const b of data.bugFixes) {
        this.db.prepare(
          "INSERT INTO bug_fixes (id, project_id, title, description, root_cause, fix, lesson, tags, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ).run(b.id, projectId, b.title, b.description, b.root_cause, b.fix, b.lesson, b.tags, b.created_at);
      }
    }
    if (data.architecture) {
      for (const a of data.architecture) {
        this.db.prepare(
          "INSERT INTO architecture (id, project_id, component, description, rationale, tags, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
        ).run(a.id, projectId, a.component, a.description, a.rationale, a.tags, a.created_at);
      }
    }
    if (data.preferences) {
      for (const p of data.preferences) {
        this.db.prepare("INSERT INTO preferences (id, project_id, key, value, created_at) VALUES (?, ?, ?, ?, ?)")
          .run(p.id, projectId, p.key, p.value, p.created_at);
      }
    }
    if (data.history) {
      for (const h of data.history) {
        this.db.prepare(
          "INSERT INTO session_history (id, project_id, session_id, action, detail, result, files_touched, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        ).run(h.id, projectId, h.session_id, h.action, h.detail, h.result, h.files_touched, h.created_at);
      }
    }

    return { imported: true, projectId };
  }

  async exportToObsidian({ project, projectPath, outputDir }) {
    const projectId = this.getOrCreateProject(project, projectPath);
    const decisions = this.db.prepare("SELECT * FROM decisions WHERE project_id = ?").all(projectId);
    const bugs = this.db.prepare("SELECT * FROM bug_fixes WHERE project_id = ?").all(projectId);

    const fs = await import("node:fs");
    const nodePath = await import("node:path");

    const outDir = outputDir || nodePath.join(process.cwd(), "docs", "decisions");
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    for (const d of decisions) {
      const fileName = d.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + ".md";
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
      fs.writeFileSync(nodePath.join(outDir, fileName), content);
    }

    for (const b of bugs) {
      const fileName = "bug-" + b.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + ".md";
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
      fs.writeFileSync(nodePath.join(outDir, fileName), content);
    }

    return { decisions: decisions.length, bugs: bugs.length, outputDir: outDir };
  }
}
