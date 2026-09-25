"""Servidor web local read-only: solo 127.0.0.1, sin mutaciones."""

from __future__ import annotations

import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import actions

from .state import get_store


HOST = "127.0.0.1"
PORT = 8765

_STATIC_ROOT = Path(__file__).resolve().parent / "web"
_INDEX_PATH = _STATIC_ROOT / "index.html"


class ControlHandler(BaseHTTPRequestHandler):
    server_version = "EcosystemControl/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[control-http] %s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, data: dict | list, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _text(self, txt: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = txt.encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _not_found(self) -> None:
        self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def _get_snapshot(self, query: str) -> "Snapshot":
        from .model import Snapshot  # local: solo por tipado
        store = get_store()
        if "refresh=1" in query:
            return store.refresh(force=True)
        return store.current()

    def do_GET(self) -> None:  # noqa: N802
        raw = self.path.split("#", 1)[0]
        path, _, query = raw.partition("?")
        if path == "/":
            if not _INDEX_PATH.exists():
                self._text("interfaz no encontrada", status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            html = _INDEX_PATH.read_text(encoding="utf-8").replace(
                "/*__CSRF__*/", f'window.CSRF={json.dumps(actions.token())};'
            )
            self._html(html)
            return
        if path == "/api/health":
            snap = self._get_snapshot(query)
            out = snap.health.to_dict()
            out["counts"] = snap.counts
            out["generated_at"] = snap.generated_at
            out["stale_seconds"] = get_store().stale_seconds()
            self._json(out)
            return
        if path == "/api/snapshot":
            snap = self._get_snapshot(query)
            out = snap.to_dict()
            out["stale_seconds"] = get_store().stale_seconds()
            self._json(out)
            return
        if path == "/api/components":
            snap = self._get_snapshot(query)
            self._json([c.to_dict() for c in snap.components])
            return
        if path == "/api/timers":
            snap = self._get_snapshot(query)
            self._json([t.to_dict() for t in snap.timers])
            return
        if path == "/api/flows":
            snap = self._get_snapshot(query)
            self._json([f.to_dict() for f in snap.flows])
            return
        if path == "/api/tasks":
            from .db import list_tasks
            from .runner import queue_summary
            limit = 50
            for part in query.split("&"):
                if part.startswith("limit="):
                    try:
                        limit = min(200, max(1, int(part[6:])))
                    except ValueError:
                        pass
            self._json({"summary": queue_summary(), "tasks": list_tasks(limit)})
            return
        if path.startswith("/api/tasks/") and path.endswith("/trace"):
            from .trace import build_trace
            try:
                tid = int(path.split("/")[3])
            except (IndexError, ValueError):
                self._json({"error": "id invalido"}, status=HTTPStatus.BAD_REQUEST)
                return
            trace = build_trace(tid)
            if trace is None:
                self._json({"error": "tarea no encontrada"},
                           status=HTTPStatus.NOT_FOUND)
                return
            self._json(trace)
            return
        if path == "/api/graph":
            from .graph import build_graph
            snap = self._get_snapshot(query)
            self._json(build_graph(snap))
            return
        if path == "/api/reconcile":
            from . import reconcile
            from .collect import ECO_ROOT
            snap = self._get_snapshot(query)
            report = reconcile.check(timers=snap.timers, eco_root=ECO_ROOT)
            self._json(report)
            return
        if path == "/api/events":
            from .db import events_for, recent_events
            kind = ""
            limit = 50
            for part in query.split("&"):
                if part.startswith("kind="):
                    kind = part[5:]
                elif part.startswith("limit="):
                    try:
                        limit = min(200, max(1, int(part[6:])))
                    except ValueError:
                        pass
            self._json(events_for(kind, limit) if kind else recent_events(limit))
            return
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            if not rel or ".." in rel:
                self._not_found()
                return
            fp = (_STATIC_ROOT / rel).resolve()
            if not str(fp).startswith(str(_STATIC_ROOT.resolve())) or not fp.is_file():
                self._not_found()
                return
            ctype, _ = mimetypes.guess_type(str(fp))
            data = fp.read_bytes()
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._not_found()

    # ---------- POST: acciones cerradas con CSRF ----------

    def _csrf_ok(self) -> bool:
        token = self.headers.get("X-CSRF-Token", "")
        if token != actions.token():
            return False
        origin = self.headers.get("Origin", "")
        if origin:
            host = urlparse(origin).netloc
            if host not in (f"{HOST}:{PORT}", "127.0.0.1:%d" % PORT, "localhost:%d" % PORT):
                return False
        return True

    def _body_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            return {}
        if length <= 0 or length > 8192:
            return {}
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def do_POST(self) -> None:  # noqa: N802
        if not self._csrf_ok():
            self._json({"error": "csrf"}, status=HTTPStatus.FORBIDDEN)
            return
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        body = self._body_json()

        if path == "/api/actions/refresh":
            self._json(actions.do_refresh())
            return
        if path == "/api/actions/run-next":
            self._json(actions.do_run_next())
            return
        if path == "/api/actions/retry":
            self._json(actions.do_retry(int(body.get("task_id", 0))))
            return
        if path == "/api/actions/cancel":
            self._json(actions.do_cancel(int(body.get("task_id", 0))))
            return
        if path == "/api/actions/add-task":
            self._json(actions.do_add_task(
                str(body.get("agent", "")), str(body.get("prompt", "")),
                str(body.get("model", "")), str(body.get("note", "")),
                str(body.get("model_policy", "paid")),
                str(body.get("sensitivity", "normal")),
            ))
            return
        if path == "/api/actions/restart":
            self._json(actions.do_restart(str(body.get("service", ""))))
            return
        # CSRF ok pero accion desconocida
        self._json({"error": "accion no permitida"}, status=HTTPStatus.BAD_REQUEST)

    def do_PUT(self) -> None:  # noqa: N802
        self._json({"error": "solo lectura"}, status=HTTPStatus.METHOD_NOT_ALLOWED)

    def do_DELETE(self) -> None:  # noqa: N802
        self._json({"error": "solo lectura"}, status=HTTPStatus.METHOD_NOT_ALLOWED)


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def run(host: str = HOST, port: int = PORT) -> None:
    srv = _Server((host, port), ControlHandler)
    sys.stderr.write(f"[ecosystem-control] escuchando en http://{host}:{port}\n")
    try:
        srv.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
