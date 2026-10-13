"""Recolecta señales observadas del ecosistema sin mutar nada."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from .model import (
    Component,
    ComponentKind,
    Flow,
    Health,
    ServiceStatus,
    Snapshot,
    Source,
    TimerInfo,
)


ECO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path.home() / ".local" / "share" / "opencode-control"
SNAPSHOT_PATH = STATE_DIR / "snapshot.json"

_SUBAGENT_NAME = re.compile(r"^###\s+(.+)$", re.MULTILINE)


def _read_skill(path: Path) -> Component | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    name = ""
    desc = ""
    for line in text.splitlines():
        l = line.strip()
        if l.startswith("name:"):
            name = l.split(":", 1)[1].strip()
        elif l.startswith("description:"):
            desc = l.split(":", 1)[1].strip()
            break
    if not name:
        name = path.parent.name
    return Component(
        kind=ComponentKind.SKILL.value,
        name=name,
        title=name,
        description=desc,
        path=str(path),
        source=Source.OBSERVADO.value,
    )


def _read_command_md(path: Path) -> Component:
    desc = ""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            l = line.strip()
            if l.startswith("description:"):
                desc = l.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return Component(
        kind=ComponentKind.COMANDO.value,
        name=path.stem,
        title=path.stem,
        description=desc,
        path=str(path),
        source=Source.OBSERVADO.value,
    )


def _collect_skills(root: Path) -> list[Component]:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []
    out: list[Component] = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if skill_md.exists():
            c = _read_skill(skill_md)
            if c:
                out.append(c)
    return out


def _collect_commands(root: Path) -> list[Component]:
    cmd_dir = root / "commands"
    if not cmd_dir.is_dir():
        return []
    return [_read_command_md(p) for p in sorted(cmd_dir.glob("*.md"))]


def _collect_scripts(root: Path) -> list[Component]:
    scripts_dir = root / "scripts"
    if not scripts_dir.is_dir():
        return []
    return [
        Component(
            kind=ComponentKind.SCRIPT.value,
            name=p.stem,
            title=p.name,
            description="",
            path=str(p),
            source=Source.OBSERVADO.value,
        )
        for p in sorted(scripts_dir.glob("*.sh"))
    ]


def _collect_root_entrypoints(root: Path) -> list[Component]:
    """Scripts de cierre en la raiz del repo (fuera de scripts/), si existen."""
    p = root / "verify.sh"
    if not p.is_file():
        return []
    return [
        Component(
            kind=ComponentKind.SCRIPT.value,
            name=p.stem,
            title=p.name,
            description="",
            path=str(p),
            source=Source.OBSERVADO.value,
        )
    ]


def _collect_memory_sh(root: Path) -> list[Component]:
    mem_dir = root / "memory"
    if not mem_dir.is_dir():
        return []
    return [
        Component(
            kind=ComponentKind.MEMORIA.value,
            name=p.stem,
            title=p.name,
            description="",
            path=str(p),
            source=Source.OBSERVADO.value,
        )
        for p in sorted(mem_dir.glob("*.sh"))
        if p.name != "MEMORY.md"
    ]


def _collect_configs(root: Path) -> list[Component]:
    cfgs: list[Component] = []
    for name in ("configs/opencode.jsonc", "configs/dcp.jsonc"):
        p = root / name
        if p.exists():
            cfgs.append(
                Component(
                    kind=ComponentKind.CONFIG.value,
                    name=p.stem,
                    title=p.name,
                    description="configuración del ecosistema",
                    path=str(p),
                    source=Source.OBSERVADO.value,
                )
            )
    return cfgs


def _parse_opencode_subagents(root: Path) -> list[Component]:
    """Extrae agentes ocultos desde configs/opencode.jsonc (observado)."""
    out: list[Component] = []
    cfg = root / "configs" / "opencode.jsonc"
    if not cfg.exists():
        return out
    try:
        text = cfg.read_text(encoding="utf-8", errors="replace")
        # Campos sencillos: name/description dentro del bloque agent.*
        for m in re.finditer(r'"([\w-]+)":\s*\{[^}]*?"description":\s*"([^"]*)"', text):
            name, desc = m.group(1), m.group(2)
            out.append(
                Component(
                    kind=ComponentKind.SUBAGENTE.value,
                    name=name,
                    title=name,
                    description=desc,
                    path=str(cfg),
                    source=Source.OBSERVADO.value,
                )
            )
    except OSError:
        pass
    return out


_TIMER_WHITELIST_PREFIXES = ("opencode-",)


def _systemd_timers() -> list[TimerInfo]:
    """Observa timers systemd --user (solo los del ecosistema, por prefijo)."""
    units: list[TimerInfo] = []
    try:
        res = subprocess.run(
            ["systemctl", "--user", "list-timers", "--output=json", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        data = json.loads(res.stdout or "[]")
        for item in data:
            unit = item.get("unit", "")
            if not unit.endswith(".timer"):
                continue
            if not unit.startswith(_TIMER_WHITELIST_PREFIXES):
                continue
            nxt = item.get("next")
            last = item.get("last")
            units.append(
                TimerInfo(
                    name=unit,
                    active=True,
                    next_run=_fmt_usec(nxt) if nxt else "",
                    last_run=_fmt_usec(last) if last else "",
                )
            )
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
        return []

    # detallar con systemctl show
    detail: list[TimerInfo] = []
    for u in units:
        try:
            res = subprocess.run(
                ["systemctl", "--user", "show", u.name, "--no-page",
                 "--property=ActiveState,SubState,Result,NextElapseUSecRealtime,LastTriggerUSec"],
                capture_output=True, text=True, timeout=5,
            )
            kv = {}
            for line in res.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    kv[k.strip()] = v.strip()
            u.active = kv.get("ActiveState") == "active"
            nr = kv.get("NextElapseUSecRealtime", "")
            lr = kv.get("LastTriggerUSec", "")
            if nr:
                u.next_run = nr
            if lr:
                u.last_run = lr
            u.result = kv.get("Result", "")
        except Exception:
            pass
        detail.append(u)
    return detail


def _declared_timer_units(root: Path) -> dict[str, str]:
    """Timers declarados en configs/cron-jobs.json -> unidad systemd esperada."""
    cfg = root / "configs" / "cron-jobs.json"
    declared: dict[str, str] = {}
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return declared
    for job in data.get("jobs", []):
        name = job.get("name", "")
        if name:
            declared[f"opencode-{name}.timer"] = job.get("schedule", "")
    return declared


def crosscheck_timers(
    declared: dict[str, str], observed: list[TimerInfo]
) -> list[str]:
    """Devuelve advertencias por divergencias config <-> systemd."""
    warnings: list[str] = []
    observed_names = {t.name for t in observed}
    for unit in declared:
        if unit not in observed_names:
            warnings.append(
                f"timer '{unit}' declarado en cron-jobs.json pero no activo en systemd"
            )
    for t in observed:
        if t.name not in declared:
            warnings.append(
                f"timer '{t.name}' activo en systemd pero no declarado en cron-jobs.json"
            )
        elif not t.active:
            warnings.append(f"timer '{t.name}' declarado pero inactivo en systemd")
    return warnings


def _fmt_usec(us: int) -> str:
    """Convierte microsegundos epoch a hora local legible."""
    try:
        import datetime as _dt
        ts = _dt.datetime.fromtimestamp(us / 1_000_000)
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(us)


def _opencode_service() -> ServiceStatus:
    """Salud del servicio OpenCode mediante CLI (observada, sin auth interna)."""
    try:
        res = subprocess.run(
            ["opencode", "service", "status"], capture_output=True, text=True, timeout=5
        )
        url = res.stdout.strip() if res.returncode == 0 else ""
        return ServiceStatus(
            active=res.returncode == 0,
            url=url,
            detail=(res.stdout + "\n" + res.stderr).strip(),
            exit_code=res.returncode,
        )
    except FileNotFoundError:
        return ServiceStatus(active=False, detail="opencode no en PATH", exit_code=127)
    except subprocess.TimeoutExpired:
        return ServiceStatus(active=False, detail="timeout", exit_code=124)


def _build_flows() -> list[Flow]:
    """Flujos declarados de alto nivel (manuales, no inferidos)."""
    return [
        Flow(
            name="odd-delegado",
            title="ODD delegado (worker → verifier)",
            description="odd/tasks/<feature>.md → odd-worker → odd-verifier",
            steps=["odd-worker", "odd-verifier"],
            source=Source.DECLARADO.value,
        ),
        Flow(
            name="odd",
            title="Flujo orgánico ODD-lite",
            description="autorizar → explorar → incertidumbre → clasificar → implementar → verificar → cerrar",
            steps=[
                "autorizar",
                "explorar",
                "resolver incertidumbre",
                "clasificar",
                "implementar",
                "verificar",
                "cerrar",
            ],
            source=Source.DECLARADO.value,
        ),
        Flow(
            name="qa-gate",
            title="Control de calidad local",
            description=(
                "qa-gate --strict sobre staged + rutas rastreadas, ejecutado siempre "
                "por el cierre ./verify.sh; ram-guard y kairos son timers, no hooks"
            ),
            steps=["qa-gate --strict (staged + rastreadas)", "ram-guard timer (5m)", "kairos timer (30m)"],
            source=Source.DECLARADO.value,
        ),
        Flow(
            name="cierre",
            title="Cierre local ./verify.sh",
            description=(
                "./verify.sh secuencial: hygiene, validate-skills (fuente y runtime), "
                "opencode debug config, status sin drift, doctores, unittest de "
                "control/tests, consulta staged y qa-gate --strict"
            ),
            steps=[
                "validate-skills (fuente + runtime)",
                "debug config",
                "status sin drift",
                "plugin doctor + context doctor",
                "unittest control/tests",
                "qa-gate --strict",
            ],
            source=Source.DECLARADO.value,
        ),
    ]


def collect_snapshot(eco_root: Path | None = None) -> Snapshot:
    root = Path(eco_root) if eco_root else ECO_ROOT
    svc = _opencode_service()
    timers = _systemd_timers()
    components: list[Component] = []
    components += _collect_skills(root)
    components += _collect_commands(root)
    components += _collect_scripts(root)
    components += _collect_root_entrypoints(root)
    components += _collect_memory_sh(root)
    components += _collect_configs(root)
    components += _parse_opencode_subagents(root)
    # Servicio OpenCode como componente también
    components.append(
        Component(
            kind=ComponentKind.SERVICIO.value,
            name="opencode",
            title="OpenCode CLI/servicio",
            description=f"Auth por pairing local. Status={'activo' if svc.active else 'inactivo'}: {svc.url}",
            path="~/.local/state/opencode/service.json",
            source=Source.OBSERVADO.value,
            tags=["opencode", "servicio"],
        )
    )
    flows = _build_flows()
    counts = {
        "skills": sum(1 for c in components if c.kind == ComponentKind.SKILL.value),
        "comandos": sum(1 for c in components if c.kind == ComponentKind.COMANDO.value),
        "scripts": sum(1 for c in components if c.kind == ComponentKind.SCRIPT.value),
        "agentes": sum(1 for c in components if c.kind == ComponentKind.SUBAGENTE.value),
        "timers": len(timers),
        "flujos": len(flows),
        "componentes": len(components),
    }
    errors = []
    warnings = crosscheck_timers(_declared_timer_units(root), timers)
    active_timers = sum(1 for t in timers if t.active)
    if not svc.active:
        errors.append("opencode service no responde exit=0")
    health = Health(
        ok=svc.active and active_timers > 0 and errors == [],
        errors=errors,
        warnings=warnings,
        open_code_active=svc.active,
        timers_active=active_timers,
        timers_total=len(timers),
    )
    snap = Snapshot(
        components=components,
        timers=timers,
        flows=flows,
        counts=counts,
        health=health,
        sources=[
            "skills/",
            "commands/",
            "configs/opencode.jsonc",
            "configs/dcp.jsonc",
            "configs/cron-jobs.json",
            "scripts/",
            "verify.sh",
            "memory/",
            "systemd --user (timers activos)",
            "opencode service status",
        ],
    )
    return snap


def write_snapshot_atomic(path: Path, snapshot: Snapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=1, sort_keys=False)
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def load_snapshot(path: Path = SNAPSHOT_PATH) -> Snapshot | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    snap = Snapshot()
    snap.version = raw.get("version", snap.version)
    snap.generated_at = raw.get("generated_at", "")
    snap.counts = raw.get("counts", {})
    snap.components = [Component(**c) for c in raw.get("components", [])]
    snap.timers = [TimerInfo(**t) for t in raw.get("timers", [])]
    snap.flows = [Flow(**f) for f in raw.get("flows", [])]
    h = raw.get("health", {})
    snap.health = Health(**{k: v for k, v in h.items() if k in Health.__dataclass_fields__})
    snap.sources = raw.get("sources", [])
    return snap
