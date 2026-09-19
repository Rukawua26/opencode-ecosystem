"""Punto de entrada del plano de control: genera snapshot o sirve web local."""

from __future__ import annotations

import argparse
import json
import sys

from .collect import SNAPSHOT_PATH
from .state import StateStore
from .server import run as run_server


def cmd_once(args: argparse.Namespace) -> int:
    store = StateStore()
    snap = store.refresh(force=True)
    if args.pretty:
        print(json.dumps(snap.to_dict(), ensure_ascii=False, indent=1))
    else:
        c = snap.counts
        print(
            f"skills={c.get('skills',0)} comandos={c.get('comandos',0)} "
            f"agentes={c.get('agentes',0)} timers={snap.health.timers_active}/{snap.health.timers_total} "
            f"opencode_activo={snap.health.open_code_active}"
        )
        print(f"snapshot: {SNAPSHOT_PATH}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    run_server(host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m control")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--once", action="store_true", help="recollecta y escribe snapshot")
    g.add_argument("--serve", action="store_true", help="sirve el panel web local")
    parser.add_argument("--pretty", action="store_true", help="pretty print JSON en --once")
    parser.add_argument("--host", default="127.0.0.1", help="host solo loopback")
    parser.add_argument("--port", type=int, default=8765)
    ns = parser.parse_args(argv)

    if ns.once:
        return cmd_once(ns)
    if ns.serve:
        return cmd_serve(ns)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
