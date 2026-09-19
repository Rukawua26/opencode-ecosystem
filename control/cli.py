"""CLI ligera del plano de control."""

from __future__ import annotations

import argparse
import json
import sys

from .db import record_receipt, recent_events
from .runner import run_next, queue_summary
from .db import add_task, list_tasks
from . import reconcile as _reconcile
from .collect import ECO_ROOT, _systemd_timers
from .state import get_store


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
    h = snap.health
    errors = [e for e in recent_events(20) if e["status"] in ("fail", "error")][:5]
    return {
        "ok": bool(h.ok and report["ok"]),
        "generated_at": snap.generated_at,
        "stale_seconds": get_store().stale_seconds(),
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
              "  doctor [--json]  diagnostico sanitizado (sin prompts ni comandos)")
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
