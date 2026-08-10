import { describe, it, beforeEach, afterEach } from "node:test";
import { strict as assert } from "node:assert";
import { MemoryAdapter } from "../src/adapter.js";
import { chmodSync, existsSync, rmSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";

const TMP_ROOT = join(tmpdir(), "opencode-test");
const TEST_DB = join(TMP_ROOT, "memory-adapter", "memory.db");

describe("MemoryAdapter", () => {
  let adapter;

  beforeEach(() => {
    const dir = dirname(TEST_DB);
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    adapter = new MemoryAdapter(TEST_DB);
    adapter.init();
  });

  afterEach(() => {
    adapter.close();
    if (existsSync(TMP_ROOT)) {
      rmSync(TMP_ROOT, { recursive: true, force: true });
    }
  });

  describe("saveDecision", () => {
    it("should create the database with user-only permissions", () => {
      if (process.platform === "win32") return;
      assert.strictEqual(statSync(TEST_DB).mode & 0o777, 0o600);
    });

    it("should not change permissions of a caller-provided directory", () => {
      if (process.platform === "win32") return;
      const customDir = join(TMP_ROOT, "memory-adapter-custom-dir");
      rmSync(customDir, { recursive: true, force: true });
      mkdirSync(customDir, { mode: 0o770 });
      chmodSync(customDir, 0o770);
      const customAdapter = new MemoryAdapter(`${customDir}/memory.db`).init();
      customAdapter.close();

      assert.strictEqual(statSync(customDir).mode & 0o777, 0o770);
      rmSync(customDir, { recursive: true, force: true });
    });

    it("should save a decision and return an id", () => {
      const result = adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        category: "architecture",
        title: "Use SQLite for memory",
        content: "We chose SQLite because it's embedded and fast.",
        rationale: "No external server needed",
        tags: "db,sqlite,memory",
      });
      assert.ok(result.id);
      assert.strictEqual(result.saved, true);
    });

    it("should retrieve saved decisions via search", () => {
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Use Redis for cache",
        content: "Redis is fast for caching",
        tags: "cache,redis",
      });

      const results = adapter.searchMemory({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        query: "redis",
      });

      assert.ok(results.decisions.length > 0);
      assert.strictEqual(results.decisions[0].title, "Use Redis for cache");
    });

    it("should reject the same project name with a different path", () => {
      adapter.saveDecision({
        project: "isolated-project",
        projectPath: join(TMP_ROOT, "project-a"),
        title: "Path A",
        content: "Bound to project A",
      });

      assert.throws(() => adapter.saveDecision({
        project: "isolated-project",
        projectPath: join(TMP_ROOT, "project-b"),
        title: "Path B",
        content: "Must not cross projects",
      }), /path mismatch/);
    });
  });

  describe("saveBugFix", () => {
    it("should save a bug fix with lesson learned", () => {
      const result = adapter.saveBugFix({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Memory leak in event listener",
        description: "Event listeners were not being cleaned up",
        rootCause: "Missing cleanup in useEffect return",
        fix: "Added cleanup function in useEffect",
        lesson: "Always return cleanup from useEffect",
        tags: "react,hooks,memory-leak",
      });
      assert.ok(result.id);
    });

    it("should find bug fixes via search", () => {
      adapter.saveBugFix({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Off by one in loop",
        description: "Loop started at 1 instead of 0",
        fix: "Changed i=1 to i=0",
        tags: "loop,bug",
      });

      const results = adapter.searchMemory({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        query: "loop",
        category: "bugs",
      });

      assert.ok(results.bugs.length > 0);
      assert.strictEqual(results.bugs[0].title, "Off by one in loop");
    });
  });

  describe("saveArchitecture", () => {
    it("should save architectural component info", () => {
      const result = adapter.saveArchitecture({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        component: "MemoryAdapter",
        description: "SQLite-based adapter for persistent memory across sessions",
        rationale: "Local-first, no external dependencies",
        tags: "core,memory",
      });
      assert.ok(result.id);
    });
  });

  describe("savePreference", () => {
    it("should save and update a preference", () => {
      adapter.savePreference({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        key: "linting",
        value: "eslint",
      });

      adapter.savePreference({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        key: "linting",
        value: "biome",
      });

      const context = adapter.getContext({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
      });

      const pref = context.preferences.find((p) => p.key === "linting");
      assert.ok(pref);
      assert.strictEqual(pref.value, "biome");
    });
  });

  describe("saveSessionAction", () => {
    it("should log a session action", () => {
      const result = adapter.saveSessionAction({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        sessionId: "abc-123",
        action: "created_file",
        detail: "Created src/index.js",
        result: "success",
        filesTouched: "src/index.js",
      });
      assert.ok(result.id);
    });
  });

  describe("getContext", () => {
    it("should return recent decisions, bugs, architecture, and preferences", () => {
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Decision 1",
        content: "First decision",
      });

      adapter.saveBugFix({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Bug 1",
        description: "A bug",
        fix: "Fixed it",
      });

      const context = adapter.getContext({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
      });

      assert.ok(context.recentDecisions.length > 0);
      assert.ok(context.recentBugs.length > 0);
    });
  });

  describe("getHistory", () => {
    it("should return session history ordered by date", () => {
      adapter.saveSessionAction({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        action: "task_start",
        detail: "Started implementing feature X",
      });

      const history = adapter.getHistory({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
      });

      assert.ok(history.length > 0);
      assert.strictEqual(history[0].action, "task_start");
    });
  });

  describe("exportProject", () => {
    it("should export all data for a project", () => {
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Export test",
        content: "Testing export",
      });

      const exported = adapter.exportProject({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
      });

      assert.ok(exported.project);
      assert.ok(exported.decisions.length > 0);
      assert.ok(Array.isArray(exported.bugFixes));
      assert.ok(Array.isArray(exported.architecture));
    });

    it("should exclude private decisions unless explicitly requested", () => {
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Public decision",
        content: "Safe to share",
      });
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Private decision",
        content: "Do not share",
        isPrivate: true,
      });

      const safeExport = adapter.exportProject({ project: "test-project", projectPath: join(TMP_ROOT, "test") });
      const fullExport = adapter.exportProject({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        includePrivate: true,
      });

      assert.deepStrictEqual(safeExport.decisions.map((decision) => decision.title), ["Public decision"]);
      assert.strictEqual(fullExport.decisions.length, 2);
    });

    it("should exclude operational records unless explicitly requested", () => {
      adapter.saveBugFix({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Sensitive operational detail",
        description: "Internal path",
        fix: "Local fix",
      });

      const safeExport = adapter.exportProject({ project: "test-project", projectPath: join(TMP_ROOT, "test") });
      const operationalExport = adapter.exportProject({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        includeOperational: true,
      });

      assert.strictEqual(safeExport.bugFixes.length, 0);
      assert.strictEqual(operationalExport.bugFixes.length, 1);
    });

    it("should import into a different project without reusing global row ids", () => {
      adapter.saveDecision({
        project: "source-project",
        projectPath: join(TMP_ROOT, "source"),
        title: "Source decision",
        content: "Portable memory",
      });
      adapter.saveDecision({
        project: "existing-project",
        projectPath: join(TMP_ROOT, "existing"),
        title: "Existing decision",
        content: "Keeps its id",
      });

      const exported = adapter.exportProject({ project: "source-project", projectPath: join(TMP_ROOT, "source") });
      exported.project.name = "imported-project";
      exported.project.path = "/tmp/imported";
      adapter.importProject(exported);

      const imported = adapter.getContext({ project: "imported-project", projectPath: "/tmp/imported" });
      assert.strictEqual(imported.recentDecisions[0].title, "Source decision");
    });

    it("should reject malformed imports before replacing existing memory", () => {
      adapter.saveDecision({
        project: "protected-project",
        projectPath: join(TMP_ROOT, "protected"),
        title: "Original decision",
        content: "Must survive a failed import",
      });
      const malformed = adapter.exportProject({
        project: "protected-project",
        projectPath: join(TMP_ROOT, "protected"),
        includeOperational: true,
      });
      malformed.decisions.push({ title: "Incomplete decision" });

      assert.throws(() => adapter.importProject(malformed), /decisions.content/);
      const context = adapter.getContext({ project: "protected-project", projectPath: join(TMP_ROOT, "protected") });
      assert.deepStrictEqual(context.recentDecisions.map((item) => item.title), ["Original decision"]);
    });

    it("should normalize a missing imported timestamp for event projection", () => {
      const data = {
        project: { name: "legacy-project", path: "/tmp/legacy-project" },
        decisions: [{
          title: "Legacy decision",
          content: "Created before event projections",
          created_at: null,
        }],
      };

      adapter.importProject(data);
      const events = adapter.listEvents({
        project: "legacy-project",
        projectPath: "/tmp/legacy-project",
        kind: "decision",
      });

      assert.strictEqual(events.length, 1);
      assert.ok(events[0].created_at);
    });
  });

  describe("searchMemory", () => {
    it("should search across all categories when no category specified", () => {
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Use PostgreSQL",
        content: "Database choice",
        tags: "db",
      });

      adapter.saveBugFix({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Connection timeout",
        description: "DB connection timeout",
        fix: "Added pool config",
        tags: "db",
      });

      const results = adapter.searchMemory({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        query: "db",
      });

      assert.ok(results.decisions.length > 0);
      assert.ok(results.bugs.length > 0);
    });

    it("should never expose private decisions through search or context", () => {
      adapter.saveDecision({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        title: "Private token rotation",
        content: "private-marker",
        isPrivate: true,
      });

      const results = adapter.searchMemory({
        project: "test-project",
        projectPath: join(TMP_ROOT, "test"),
        query: "private-marker",
        semantic: false,
      });
      const context = adapter.getContext({ project: "test-project", projectPath: join(TMP_ROOT, "test") });

      assert.strictEqual(results.decisions.length, 0);
      assert.strictEqual(context.recentDecisions.length, 0);
    });
  });

  describe("memory events", () => {
    it("filters events by kind and excludes private decisions by default", () => {
      adapter.saveDecision({
        project: "event-project",
        projectPath: join(TMP_ROOT, "events"),
        title: "Public event",
        content: "Shareable",
        tags: "feature:001,receipt:r1",
      });
      adapter.saveDecision({
        project: "event-project",
        projectPath: join(TMP_ROOT, "events"),
        title: "Private event",
        content: "Secret",
        isPrivate: true,
      });
      adapter.saveBugFix({
        project: "event-project",
        projectPath: join(TMP_ROOT, "events"),
        title: "Bug event",
        description: "Broken",
        fix: "Fixed",
      });

      const safe = adapter.listEvents({
        project: "event-project",
        projectPath: join(TMP_ROOT, "events"),
        kind: "decision",
      });
      const complete = adapter.listEvents({
        project: "event-project",
        projectPath: join(TMP_ROOT, "events"),
        kind: "decision",
        includePrivate: true,
      });

      assert.deepStrictEqual(safe.map((event) => event.content.title), ["Public event"]);
      assert.strictEqual(complete.length, 2);
      assert.deepStrictEqual(safe[0].tags, [["feature", "001"], ["receipt", "r1"]]);
    });

    it("applies limits and date filters before returning projected events", () => {
      for (const title of ["One", "Two", "Three"]) {
        adapter.saveDecision({
          project: "limited-project",
          projectPath: join(TMP_ROOT, "limited"),
          title,
          content: title,
        });
      }

      assert.strictEqual(adapter.listEvents({
        project: "limited-project",
        projectPath: join(TMP_ROOT, "limited"),
        kind: "decision",
        limit: 2,
      }).length, 2);
      assert.deepStrictEqual(adapter.listEvents({
        project: "limited-project",
        projectPath: join(TMP_ROOT, "limited"),
        since: "2999-01-01T00:00:00Z",
      }), []);
      assert.throws(() => adapter.listEvents({
        project: "limited-project",
        projectPath: join(TMP_ROOT, "limited"),
        since: "not-a-date",
      }), /invalid: since/);
      assert.throws(() => adapter.listEvents({
        project: "limited-project",
        projectPath: join(TMP_ROOT, "limited"),
        since: "2026-02-30",
      }), /invalid: since/);
    });

    it("treats stored timestamps as UTC and date-only until as end of day", () => {
      const saved = adapter.saveDecision({
        project: "date-project",
        projectPath: join(TMP_ROOT, "dates"),
        title: "Boundary event",
        content: "UTC timestamp",
      });
      adapter.db.prepare("UPDATE decisions SET created_at = ? WHERE id = ?")
        .run("2026-08-10 21:01:47", saved.id);

      const base = {
        project: "date-project",
        projectPath: join(TMP_ROOT, "dates"),
        kind: "decision",
      };
      assert.strictEqual(adapter.listEvents({ ...base, since: "2026-08-10 21:01:47" }).length, 1);
      assert.strictEqual(adapter.listEvents({ ...base, until: "2026-08-10" }).length, 1);
      assert.strictEqual(adapter.listEvents({ ...base, since: "2026-08-11" }).length, 0);
    });

    it("projects legacy rows with null timestamps without failing the project", () => {
      const projectPath = join(TMP_ROOT, "legacy-null");
      const projectId = adapter.getOrCreateProject("legacy-null-project", projectPath);
      adapter.db.prepare(
        "INSERT INTO decisions (project_id, title, content, created_at) VALUES (?, ?, ?, NULL)",
      ).run(projectId, "Legacy null date", "Still readable");

      const events = adapter.listEvents({
        project: "legacy-null-project",
        projectPath,
        kind: "decision",
      });
      assert.strictEqual(events[0].created_at, "1970-01-01 00:00:00");
    });

    it("exports and validates canonical JSONL", () => {
      adapter.saveArchitecture({
        project: "jsonl-project",
        projectPath: join(TMP_ROOT, "jsonl"),
        component: "Memory events",
        description: "Canonical projection",
        tags: "feature:001,lens:architecture-review",
      });

      const jsonl = adapter.exportEventsJsonl({
        project: "jsonl-project",
        projectPath: join(TMP_ROOT, "jsonl"),
      });
      const events = adapter.validateEventsJsonl(jsonl);

      assert.strictEqual(events.length, 1);
      assert.strictEqual(events[0].kind, "architecture");
      assert.throws(
        () => adapter.validateEventsJsonl(jsonl.replace("Canonical projection", "Modified")),
        /hash mismatch/,
      );
    });
  });
});
