"""CLI ligera del plano de control."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from .db import get_task, latest_child_task, next_pending, record_receipt, recent_events
from .runner import run_next, queue_summary
from .db import add_task, list_tasks
from . import reconcile as _reconcile
from .collect import ECO_ROOT, _systemd_timers
from .state import get_store


_OPENCODE_REQUIRED = "2.x"
_OPENCODE_CAPABILITIES = ("run", "debug_config", "service_status")
_TASK_RUN_TRANSITION = "python3 -m control.cli task run"


def _opencode_diagnostic() -> dict:
    """Comprueba OpenCode bajo demanda sin exponer su salida completa."""
    available = True
    version = None
    compatible = False
    try:
        proc = subprocess.run(
            ["opencode", "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=3, check=False,
        )
    except (FileNotFoundError, OSError):
        available = False
    except (subprocess.TimeoutExpired, UnicodeError):
        pass
    else:
        output = "\n".join(
            part for part in (proc.stdout, proc.stderr) if part
        ).strip()
        match = re.fullmatch(
            r"opencode[ \t]+v([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})",
            output,
            flags=re.IGNORECASE,
        )
        if match:
            parts = tuple(int(part) for part in match.groups())
            version = ".".join(str(part) for part in parts)
            compatible = proc.returncode == 0 and parts[0] == 2
    return {
        "available": available,
        "version": version,
        "compatible": compatible,
        "required": _OPENCODE_REQUIRED,
        "capabilities": {
            capability: compatible for capability in _OPENCODE_CAPABILITIES
        },
    }


def cmd_status() -> int:
    snap = get_store().refresh(force=True)
    health = snap.health
    print(f"[control] skills={snap.counts.get('skills', 0)} "
          f"comandos={snap.counts.get('comandos', 0)} "
          f"agentes={snap.counts.get('agentes', 0)} "
          f"timers={health.timers_active}/{health.timers_total} "
          f"opencode_activo={health.open_code_active}")
    if health.errors:
        for e in health.errors:
            print(f"  ERROR: {e}")
    return 0 if health.ok else 1


def cmd_receipt(args: list[str]) -> int:
    p = argparse.ArgumentParser(prog="control receipt",
                                description="registra un recibo de ejecucion real")
    p.add_argument("component", help="skill/agente/timer/script ejecutado")
    p.add_argument("--status", choices=["ok", "fail", "skipped"], default="ok")
    p.add_argument("--duration", type=float, default=0.0, help="segundos")
    p.add_argument("--note", default="", help="resumen corto (sin secretos)")
    ns = p.parse_args(args)
    if len(ns.note) > 200:
        print("nota demasiado larga (max 200)", file=sys.stderr)
        return 2
    record_receipt(ns.component, ns.status, ns.duration, ns.note)
    print(f"[control] recibo registrado: {ns.component} status={ns.status}")
    return 0


def assess_task(task_id: int, path: Path | None = None) -> dict:
    """Informa del estado de revision ODD usando solo estado ya persistido."""
    worker = get_task(task_id, path)
    if worker is None:
        raise ValueError("la tarea no existe")
    if worker["agent"] != "odd-worker":
        raise ValueError("la tarea no pertenece a odd-worker")

    verifier = latest_child_task(task_id, "odd-verifier", path)
    worker_status = worker["status"]
    review_due = str(worker.get("finished_at") or "") if worker_status == "done" else ""
    review_state = "pending"
    next_transition = ""
    reason = "worker no terminado"

    if worker_status == "dead":
        review_state, reason = "failed", "worker dead"
    elif worker_status == "done" and verifier is None:
        review_state, reason = "due", "verificador ausente"
    elif worker_status == "done":
        verifier_status = verifier["status"]
        if verifier_status == "pending":
            review_state = "due"
            queued = next_pending(path)
            if queued and queued["id"] == verifier["id"]:
                next_transition = _TASK_RUN_TRANSITION
                reason = "verificador pendiente"
            else:
                reason = "verificador espera turno"
        elif verifier_status == "running":
            reason = "verificador en curso"
        elif verifier_status == "waiting":
            reason = "verificador esperando decision"
        elif verifier_status == "done":
            review_state, reason = "passed", "verificacion aprobada"
        elif verifier_status == "dead":
            review_state, reason = "failed", "verificacion fallida"
        else:
            reason = "estado de verificador no terminal"

    return {
        "task_id": task_id,
        "verifier_id": verifier["id"] if verifier else None,
        "review_state": review_state,
        "review_due": review_due,
        "next_transition": next_transition,
        "reason": reason,
    }


def cmd_task(args: list[str]) -> int:
    p = argparse.ArgumentParser(prog="control task",
                                description="cola de tareas del lanzador")
    sub = p.add_subparsers(dest="action", required=True)
    pa = sub.add_parser("add", help="encola una tarea")
    pa.add_argument("agent")
    pa.add_argument("prompt")
    pa.add_argument("--note", default="")
    pa.add_argument("--model", default="", help="ej. opencode/nemotron-3-ultra-free")
    pa.add_argument("--workflow", default="")
    pa.add_argument("--workspace", default="")
    pa.add_argument("--feature", default="")
    pa.add_argument("--expected-outputs", default="")
    pa.add_argument("--verification-command", default="")
    pa.add_argument("--model-policy", choices=["paid", "free-allowed"], default="paid")
    pa.add_argument("--sensitivity", choices=["normal", "sensitive"], default="normal")
    pl = sub.add_parser("list", help="lista la cola")
    pl.add_argument("--limit", type=int, default=20)
    sub.add_parser("run", help="ejecuta la primera tarea pendiente (1 a la vez)")
    assess = sub.add_parser(
        "assess", help="informa la revision de un odd-worker sin ejecutarla"
    )
    assess.add_argument("worker_id", type=int, help="id de la tarea odd-worker")
    ns = p.parse_args(args)

    if ns.action == "add":
        try:
            tid = add_task(
                ns.agent, ns.prompt, ns.note, ns.model,
                workflow=ns.workflow,
                workspace=ns.workspace,
                feature=ns.feature,
                expected_outputs=ns.expected_outputs,
                verification_command=ns.verification_command,
                model_policy=ns.model_policy,
                sensitivity=ns.sensitivity,
            )
        except ValueError as exc:
            print(f"[control] tarea rechazada: {exc}", file=sys.stderr)
            return 2
        print(f"[control] tarea #{tid} encolada (agente={ns.agent})")
        return 0
    if ns.action == "list":
        rows = list_tasks(ns.limit)
        if not rows:
            print("(cola vacia)")
        for t in rows:
            print(f"#{t['id']:>3} {t['status']:<8} {t['agent']:<16} "
                  f"intentos={t['attempts']} rc={t['result_code']} "
                  f"model={t.get('model') or '(default)'}")
        s = queue_summary()
        print(f"resumen: {s}")
        return 0
    if ns.action == "assess":
        try:
            result = assess_task(ns.worker_id)
        except ValueError as exc:
            print(f"[control] assess rechazado: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0
    # run
    t = run_next()
    if t is None:
        print("(cola vacia)")
        return 0
    print(f"task #{t['id']} -> {t['status']} (rc={t.get('result_code')})")
    return 0 if t.get("status") == "done" else 1


def doctor_dict() -> dict:
    """Diagnostico sanitizado: nunca incluye prompt, workspace ni comandos."""
    snap = get_store().refresh()
    timers = _systemd_timers()
    report = _reconcile.check(timers=timers, eco_root=ECO_ROOT)
    opencode = _opencode_diagnostic()
    h = snap.health
    errors = [e for e in recent_events(20) if e["status"] in ("fail", "error")][:5]
    return {
        "ok": bool(h.ok and report["ok"] and opencode["compatible"]),
        "generated_at": snap.generated_at,
        "stale_seconds": get_store().stale_seconds(),
        "opencode": opencode,
        "health": {
            "ok": h.ok,
            "errors": h.errors,
            "warnings": h.warnings,
            "opencode_active": h.open_code_active,
            "timers_active": h.timers_active,
            "timers_total": h.timers_total,
        },
        "queue": queue_summary(),
        "reconcile": {
            "ok": report["ok"],
            "findings": [f'{f["kind"]}: {f["target"]}' for f in report["findings"]],
        },
        "recent_errors": [
            {"ts": e["ts"], "kind": e["kind"], "event": e["event"], "status": e["status"]}
            for e in errors
        ],
    }


def cmd_doctor(as_json: bool) -> int:
    d = doctor_dict()
    if as_json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0 if d["ok"] else 1
    print(f"[doctor] ok={d['ok']} snapshot={d['generated_at']} "
          f"(hace {d['stale_seconds']:.0f}s)")
    opencode = d["opencode"]
    capabilities = " ".join(
        f"{name}={enabled}"
        for name, enabled in opencode["capabilities"].items()
    )
    print(f"  opencode: available={opencode['available']} "
          f"version={opencode['version']} compatible={opencode['compatible']} "
          f"required={opencode['required']} capacidades=({capabilities})")
    h = d["health"]
    print(f"  salud: ok={h['ok']} opencode_activo={h['opencode_active']} "
          f"timers={h['timers_active']}/{h['timers_total']}")
    for e in h["errors"]:
        print(f"  ERROR: {e}")
    for w in h["warnings"]:
        print(f"  WARN: {w}")
    print(f"  cola: {d['queue']}")
    r = d["reconcile"]
    print(f"  reconciliador: ok={r['ok']}"
          + ("" if r["ok"] else f" findings={r['findings']}"))
    if d["recent_errors"]:
        print("  ultimos errores:")
        for e in d["recent_errors"]:
            print(f"    {e['ts']} {e['kind']}/{e['event']} -> {e['status']}")
    return 0 if d["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] == "status":
        return cmd_status()
    if args[0] == "snapshot":
        snap = get_store().refresh(force=True)
        print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=1))
        return 0
    if args[0] == "receipt":
        return cmd_receipt(args[1:])
    if args[0] == "task":
        return cmd_task(args[1:])
    if args[0] == "doctor":
        return cmd_doctor("--json" in args[1:])
    if args[0] in ("-h", "--help"):
        print("uso: python3 -m control.cli "
              "[status|snapshot|receipt|task|doctor|reconcile]\n"
              "  doctor [--json]  diagnostico OpenCode V2 sanitizado")
        return 0
    if args[0] == "reconcile":
        mode_apply = "--apply" in args[1:]
        report = _reconcile.check(timers=_systemd_timers(), eco_root=ECO_ROOT)
        if mode_apply and not report["ok"]:
            report = _reconcile.apply_fixes(report)
        print(f"[reconcile] ts={report['ts']} "
              f"findings={len(report['findings'])} ok={report['ok']}")
        for f in report["findings"]:
            print(f"  - {f['kind']}: {f['target']} -> {f['action']}"
                  + (f" ({f['detail']})" if f["detail"] else ""))
        if "apply" in report:
            print(f"  apply: {report['apply']}"
                  + (f" aplicadas={report.get('applied')}" if report.get("applied") else ""))
        return 0 if report["ok"] else 1
    print("uso: python3 -m control.cli "
          "[status|snapshot|receipt|task|doctor|reconcile]",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
