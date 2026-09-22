"""E2E opt-in (T16): control-plane + OpenCode real con proveedor simulado.

Solo se ejecuta con OPENCODE_E2E=1 (se salta en la suite normal). Reutiliza el
patron del spike validado (/tmp/opencode/e2e-spike/run_spike.py): mock SSE en
loopback, HOME/XDG temporales, proxy muerto para todo menos 127.0.0.1, DB
efimera. Sin tokens, sin red externa, sin npm bootstrap. Fuera de verify.sh.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from control import cli, db, runner

RESPONSE_TEXT = "SUMMARY: ok mock determinista\nRESULT: success"
DEAD_PROXY = "http://127.0.0.1:9"
E2E_REASON = "E2E OpenCode real opt-in: ejecutar con OPENCODE_E2E=1"


class MockProviderHandler(BaseHTTPRequestHandler):
    """Patron SSE del spike: streaming si el body trae stream:true, JSON si no."""

    requests: list[tuple[str, bool]] = []  # (path, streamed) solo chat completions

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            req = {}
        if not self.path.endswith("/chat/completions"):
            self.send_response(404)
            self.end_headers()
            return
        streamed = bool(req.get("stream"))
        MockProviderHandler.requests.append((self.path, streamed))
        base = {"id": "chatcmpl-mock-1", "created": 1234567890, "model": "test"}
        if streamed:
            chunks = [
                {**base, "object": "chat.completion.chunk", "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None,
                }]},
                {**base, "object": "chat.completion.chunk", "choices": [{
                    "index": 0,
                    "delta": {"content": RESPONSE_TEXT},
                    "finish_reason": None,
                }]},
                {**base, "object": "chat.completion.chunk", "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1,
                              "total_tokens": 2},
                },
            ]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            for chunk in chunks:
                self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            return
        payload = {
            **base,
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": RESPONSE_TEXT},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


def build_config(port: int) -> str:
    """Config aislada del spike + agentes odd-worker/odd-verifier del E2E."""
    return json.dumps({
        "$schema": "https://opencode.ai/config.json",
        "model": "mock/test",
        "providers": {
            "mock": {
                "name": "Mock",
                "env": ["MOCK_API_KEY"],
                "package": "@opencode/ai/providers/openai-compatible",
                "settings": {"baseURL": f"http://127.0.0.1:{port}/v1"},
                "models": {"test": {"name": "Mock Test"}},
            },
        },
        "agents": {
            "odd-worker": {
                "mode": "subagent",
                "hidden": True,
                "model": "mock/test",
                "description": "Ejecutor ODD del E2E",
                "system": "Responde siempre con el contrato pedido. No modifiques archivos.",
                "permissions": [
                    { "action": "subagent", "resource": "*", "effect": "deny" }
                ],
            },
            "odd-verifier": {
                "mode": "subagent",
                "hidden": True,
                "model": "mock/test",
                "description": "Verificador ODD del E2E",
                "system": "Verifica y responde con el contrato pedido. No modifiques archivos.",
                "permissions": [
                    { "action": "edit", "resource": "*", "effect": "deny" },
                    { "action": "subagent", "resource": "*", "effect": "deny" }
                ],
            },
        },
    }, indent=1)


@unittest.skipUnless(os.environ.get("OPENCODE_E2E") == "1", E2E_REASON)
class TestE2EReal(unittest.TestCase):
    """Recorrido real del control-plane con OpenCode real offline (T16)."""

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.home = Path(self.td.name)
        self.workspace = self.home / "workspace"
        self.config_dir = self.home / ".config" / "opencode"
        self.config_dir.mkdir(parents=True)
        self.workspace.mkdir()
        self.db_path = self.home / "control.db"
        db.init_db(self.db_path)
        # Wrapper efimero de opencode en PATH: anade --standalone a `run` y
        # ejecuta el binario real; el lanzador de produccion no cambia.
        self.bin_dir = self.home / "bin"
        self.bin_dir.mkdir()
        real = shutil.which("opencode")
        if real is None:
            self.fail("opencode no disponible para el E2E opt-in")
        binary = shlex.quote(real)
        shim = self.bin_dir / "opencode"
        shim.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "run" ]; then\n'
            "    shift\n"
            f'    exec {binary} run --standalone "$@"\n'
            "fi\n"
            f'exec {binary} "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MockProviderHandler)
        self.addCleanup(self._stop_server)
        MockProviderHandler.requests = []
        config_path = self.config_dir / "opencode.jsonc"
        config_path.write_text(build_config(self.server.server_port), encoding="utf-8")

    def _stop_server(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def test_recorrido_real(self) -> None:
        worker_id = db.add_task(
            "odd-worker", "Di un saludo corto y escribe el contrato ODD",
            model="mock/test", workflow="odd", feature="e2e-mock",
            workspace=str(self.workspace), verification_command="true",
            path=self.db_path,
        )
        threading.Thread(
            target=self.server.serve_forever, daemon=True
        ).start()
        saved = dict(os.environ)
        try:
            os.environ.update({
                "HOME": str(self.home),
                "PATH": f"{self.bin_dir}:{saved.get('PATH', '')}",
                "XDG_CONFIG_HOME": str(self.home / ".config"),
                "XDG_DATA_HOME": str(self.home / ".local" / "share"),
                "XDG_CACHE_HOME": str(self.home / ".cache"),
                "XDG_STATE_HOME": str(self.home / ".local" / "state"),
                "OPENCODE_CONFIG_DIR": str(self.config_dir),
                "MOCK_API_KEY": "dummy",
                "OPENCODE_DISABLE_MODELS_FETCH": "1",
                "HTTP_PROXY": DEAD_PROXY, "HTTPS_PROXY": DEAD_PROXY,
                "ALL_PROXY": DEAD_PROXY,
                "http_proxy": DEAD_PROXY, "https_proxy": DEAD_PROXY,
                "all_proxy": DEAD_PROXY,
                "NO_PROXY": "127.0.0.1,localhost,::1",
                "no_proxy": "127.0.0.1,localhost,::1",
            })
            worker = runner.run_next(self.db_path)
            verifier = runner.run_next(self.db_path)
            review = cli.assess_task(worker_id, self.db_path)

            # worker done con recibo y verifier unico encadenado (parent_id)
            self.assertEqual(worker["status"], "done")
            self.assertEqual(worker["result_code"], 0)
            self.assertEqual(verifier["status"], "done")
            self.assertEqual(verifier["result_code"], 0)
            public = db.list_tasks(200, path=self.db_path)
            verifiers = [r for r in public if r["agent"] == "odd-verifier"]
            self.assertEqual(len(verifiers), 1)
            self.assertEqual(verifiers[0]["parent_id"], worker_id)

            # verifier done: check determinista rc=0 + recibo (worker y verifier)
            events = db.recent_events(50, path=self.db_path)
            self.assertTrue(any(
                r["category"] == "verification" and r["event"] == "check determinista"
                for r in events
            ))
            receipts = [r for r in events if r["category"] == "receipt"]
            self.assertEqual(len(receipts), 2)
            self.assertTrue(all(r["status"] == "success" for r in receipts))

            # assess del worker -> passed
            self.assertEqual(review["review_state"], "passed")
            self.assertEqual(review["verifier_id"], verifiers[0]["id"])

            # sin acceso externo exitoso: solo loopback alcanzo el mock y el
            # texto determinista confirma que las respuestas salieron de el.
            chat = MockProviderHandler.requests
            self.assertGreaterEqual(len(chat), 2)
            self.assertTrue(all(p.endswith("/chat/completions") for p, _ in chat))

            # sin stdout completo ni secretos en DB (solo columnas publicas)
            for row in public:
                self.assertFalse({"prompt", "workspace", "verification_command",
                                  "expected_outputs"} & set(row))
                for value in row.values():
                    self.assertNotIn("dummy", str(value))
                    self.assertNotIn("RESULT:", str(value))
            notes = {r["agent"]: r["note"] for r in public}
            self.assertEqual(notes.get("odd-worker"), "ok mock determinista")
            self.assertEqual(notes.get("odd-verifier"), "ok mock determinista")
        finally:
            os.environ.clear()
            os.environ.update(saved)


if __name__ == "__main__":
    unittest.main()
