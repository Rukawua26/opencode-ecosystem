"""SQLite local: eventos sin prompts y cola con payload minimizado."""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(
    os.environ.get("OPENCODE_CONTROL_DB")
    or (Path.home() / ".local" / "share" / "opencode-control" / "control.db")
)

_MAX_DETAIL = 300
_MAX_ROWS = 20_000
_RETENTION_DAYS = 30

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    category TEXT NOT NULL,
    event TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    duration_s REAL
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_kind_ts ON events(kind, ts DESC);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    result_code INTEGER,
    note TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    workflow TEXT NOT NULL DEFAULT '',
    workspace TEXT NOT NULL DEFAULT '',
    feature TEXT NOT NULL DEFAULT '',
    expected_outputs TEXT NOT NULL DEFAULT '',
    verification_command TEXT NOT NULL DEFAULT '',
    model_policy TEXT NOT NULL DEFAULT 'paid',
    sensitivity TEXT NOT NULL DEFAULT 'normal',
    parent_id INTEGER,
    lease_owner TEXT NOT NULL DEFAULT '',
    lease_until TEXT NOT NULL DEFAULT '',
    error_kind TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, id);
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Migraciones incrementales idempotentes."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()}
    # columna -> (DDL de la columna). Se añade solo si falta.
    additions = {
        "model": "ALTER TABLE tasks ADD COLUMN model TEXT NOT NULL DEFAULT ''",
        "workflow": "ALTER TABLE tasks ADD COLUMN workflow TEXT NOT NULL DEFAULT ''",
        "workspace": "ALTER TABLE tasks ADD COLUMN workspace TEXT NOT NULL DEFAULT ''",
        "feature": "ALTER TABLE tasks ADD COLUMN feature TEXT NOT NULL DEFAULT ''",
        "expected_outputs": "ALTER TABLE tasks ADD COLUMN expected_outputs TEXT NOT NULL DEFAULT ''",
        "verification_command": "ALTER TABLE tasks ADD COLUMN verification_command TEXT NOT NULL DEFAULT ''",
        "model_policy": "ALTER TABLE tasks ADD COLUMN model_policy TEXT NOT NULL DEFAULT 'paid'",
        "sensitivity": "ALTER TABLE tasks ADD COLUMN sensitivity TEXT NOT NULL DEFAULT 'normal'",
        "parent_id": "ALTER TABLE tasks ADD COLUMN parent_id INTEGER",
        "lease_owner": "ALTER TABLE tasks ADD COLUMN lease_owner TEXT NOT NULL DEFAULT ''",
        "lease_until": "ALTER TABLE tasks ADD COLUMN lease_until TEXT NOT NULL DEFAULT ''",
        "error_kind": "ALTER TABLE tasks ADD COLUMN error_kind TEXT NOT NULL DEFAULT ''",
    }
    for col, ddl in additions.items():
        if col not in cols:
            conn.execute(ddl)
    conn.execute(
        "INSERT INTO schema_meta(key, value) VALUES('schema_version', '2') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )


def _purge_old_task_payloads(conn: sqlite3.Connection) -> None:
    """Borra payload operativo normal 30d después de terminar."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)).isoformat()
    conn.execute(
        "UPDATE tasks SET prompt='[purged]', workspace='', expected_outputs='', "
        "verification_command='' WHERE status IN ('done','dead') "
        "AND finished_at IS NOT NULL AND finished_at < ? AND prompt != '[purged]'",
        (cutoff,),
    )

_lock = threading.Lock()


def _connect(path: Path | None = None) -> sqlite3.Connection:
    db = path or DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(path: Path | None = None) -> None:
    with _lock, _connect(path) as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)
        _purge_old_task_payloads(conn)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_event(
    kind: str,
    category: str,
    event: str,
    status: str = "",
    detail: str = "",
    duration_s: float | None = None,
    path: Path | None = None,
) -> None:
    """Registra un evento. `detail` se trunca; jamas guardar prompts ni secretos."""
    init_db(path)
    detail = (detail or "")[:_MAX_DETAIL]
    with _lock, _connect(path) as conn:
        conn.execute(
            "INSERT INTO events (ts, kind, category, event, status, detail, duration_s)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (_now(), kind, category, event, status, detail, duration_s),
        )
        n = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        if n > _MAX_ROWS:
            conn.execute(
                "DELETE FROM events WHERE id NOT IN"
                " (SELECT id FROM events ORDER BY id DESC LIMIT ?)",
                (_MAX_ROWS,),
            )
        cutoff = (datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)).isoformat()
        conn.execute("DELETE FROM events WHERE ts < ?", (cutoff,))


def record_receipt(
    component: str,
    status: str,
    duration_s: float,
    note: str = "",
    path: Path | None = None,
) -> None:
    """Recibo explicito de ejecucion (tarea o componente ejecutado de verdad)."""
    record_event(
        kind=component,
        category="receipt",
        event="ejecutado",
        status=status,
        detail=note,
        duration_s=duration_s,
        path=path,
    )


def recent_events(limit: int = 50, path: Path | None = None) -> list[dict]:
    init_db(path)
    with _lock, _connect(path) as conn:
        rows = conn.execute(
            "SELECT ts, kind, category, event, status, detail, duration_s"
            " FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def events_for(kind: str, limit: int = 30, path: Path | None = None) -> list[dict]:
    init_db(path)
    with _lock, _connect(path) as conn:
        rows = conn.execute(
            "SELECT ts, kind, category, event, status, detail, duration_s"
            " FROM events WHERE kind = ? ORDER BY id DESC LIMIT ?",
            (kind, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- cola de tareas (Etapa 3) ----------

_MAX_PROMPT = 4000


def _validate_task_policy(model: str, model_policy: str, sensitivity: str) -> None:
    if model_policy not in {"paid", "free-allowed"}:
        raise ValueError("model_policy debe ser paid o free-allowed")
    if sensitivity not in {"normal", "sensitive"}:
        raise ValueError("sensitivity debe ser normal o sensitive")
    is_free = "free" in model.casefold()
    if is_free and model_policy != "free-allowed":
        raise ValueError("modelo free requiere model_policy=free-allowed")
    if is_free and sensitivity == "sensitive":
        raise ValueError("tarea sensitive no puede usar modelo free")


def add_task(
    agent: str,
    prompt: str,
    note: str = "",
    model: str = "",
    path: Path | None = None,
    **contract: str,
) -> int:
    """Encola una tarea. `contract`): workflow, workspace, feature,
    expected_outputs, verification_command, model_policy, sensitivity, parent_id.
    """
    if not agent or not prompt:
        raise ValueError("agent y prompt son obligatorios")
    model_policy = str(contract.get("model_policy", "paid"))
    sensitivity = str(contract.get("sensitivity", "normal"))
    _validate_task_policy(model, model_policy, sensitivity)
    init_db(path)
    fields = {
        "prompt": prompt[:_MAX_PROMPT],
        "note": note[:_MAX_DETAIL],
        "model": model,
        "created_at": _now(),
    }
    for k in ("workflow", "workspace", "feature", "expected_outputs",
              "verification_command", "model_policy", "sensitivity", "parent_id"):
        if k in contract:
            fields[k] = contract[k]
    cols = ["agent", *fields.keys()]
    placeholders = ", ".join("?" for _ in cols)
    with _lock, _connect(path) as conn:
        cur = conn.execute(
            f"INSERT INTO tasks ({', '.join(cols)}) VALUES ({placeholders})",
            (agent, *fields.values()),
        )
        return int(cur.lastrowid)


def next_pending(path: Path | None = None) -> dict | None:
    init_db(path)
    with _lock, _connect(path) as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY id LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def update_task(task_id: int, path: Path | None = None, **fields: object) -> None:
    allowed = {"status", "attempts", "started_at", "finished_at", "result_code",
               "note", "lease_owner", "lease_until", "error_kind",
               "workflow", "workspace", "feature", "expected_outputs",
               "verification_command", "model_policy", "sensitivity", "parent_id"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    init_db(path)
    cols = ", ".join(f"{k} = ?" for k in sets)
    with _lock, _connect(path) as conn:
        conn.execute(f"UPDATE tasks SET {cols} WHERE id = ?", (*sets.values(), task_id))


def scrub_task_payload(task_id: int, path: Path | None = None) -> None:
    """Minimiza inmediatamente una tarea sensible ya terminal."""
    init_db(path)
    with _lock, _connect(path) as conn:
        conn.execute(
            "UPDATE tasks SET prompt='[purged]', workspace='', expected_outputs='', "
            "verification_command='' WHERE id=? AND status IN ('done','dead')",
            (task_id,),
        )


_PUBLIC_TASK_COLUMNS = (
    "id, agent, status, attempts, created_at, started_at, finished_at, "
    "result_code, note, model, workflow, feature, model_policy, sensitivity, "
    "parent_id, lease_owner, lease_until, error_kind"
)


def list_tasks(
    limit: int = 50,
    path: Path | None = None,
    include_private: bool = False,
) -> list[dict]:
    """Lista tareas. Por defecto omite prompt, workspace y comandos."""
    init_db(path)
    columns = "*" if include_private else _PUBLIC_TASK_COLUMNS
    with _lock, _connect(path) as conn:
        rows = conn.execute(
            f"SELECT {columns} FROM tasks ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_task(task_id: int, path: Path | None = None) -> dict | None:
    """Obtiene una tarea por id sin exponer su payload privado."""
    init_db(path)
    with _lock, _connect(path) as conn:
        row = conn.execute(
            f"SELECT {_PUBLIC_TASK_COLUMNS} FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return dict(row) if row else None


def latest_child_task(
    parent_id: int,
    agent: str,
    path: Path | None = None,
) -> dict | None:
    """Obtiene el hijo mas reciente de un agente sin campos privados."""
    init_db(path)
    with _lock, _connect(path) as conn:
        row = conn.execute(
            f"SELECT {_PUBLIC_TASK_COLUMNS} FROM tasks "
            "WHERE parent_id = ? AND agent = ? ORDER BY id DESC LIMIT 1",
            (parent_id, agent),
        ).fetchone()
    return dict(row) if row else None


def claim_next(owner: str, lease_s: int, path: Path | None = None) -> dict | None:
    """Reclamo atómico de la primera tarea pending.

    thread- Y process-safe: BEGIN IMMEDIATE garantiza que solo uno gana.
    Devuelve la tarea ya marcada running con lease, o None.
    """
    init_db(path)
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat(timespec="seconds")
    lease_until = (now_dt.timestamp() + lease_s)
    lease_iso = datetime.fromtimestamp(lease_until, tz=timezone.utc).isoformat(timespec="seconds")
    with _lock:
        conn = _connect(path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM tasks WHERE status = 'pending' ORDER BY id LIMIT 1"
            ).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                return None
            conn.execute(
                "UPDATE tasks SET status='running', attempts=attempts+1,"
                " started_at=?, lease_owner=?, lease_until=? WHERE id=?",
                (now, owner, lease_iso, row["id"]),
            )
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
        # devolver estado actualizado desde una conexión limpia
        with _connect(path) as conn2:
            after = conn2.execute(
                "SELECT * FROM tasks WHERE id=?", (row["id"],)
            ).fetchone()
        return dict(after) if after else None
