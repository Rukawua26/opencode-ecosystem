"""Modelo de datos del plano de control local (stdlib)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Source(str, Enum):
    """Procedencia del dato. Marca honestidad del panel."""

    OBSERVADO = "observado"     # leído directamente del sistema (fs, systemd, CLI)
    DECLARADO = "declarado"     # del manifiesto/catalogo explícito
    INFERIDO = "inferido"       # deducido, caveat
    DESCONOCIDO = "desconocido"  # sin evidencia


class ComponentKind(str, Enum):
    SKILL = "skill"
    COMANDO = "comando"
    SUBAGENTE = "agente"
    SCRIPT = "script"
    MEMORIA = "memoria"
    CONFIG = "config"
    TIMER = "timer"
    SERVICIO = "servicio"
    DIRECTORIO = "directorio"
    OTRO = "otro"


@dataclass(slots=True)
class Component:
    """Un elemento del ecosistema: skill, comando, agente, script, etc."""

    kind: str
    name: str
    title: str = ""
    description: str = ""
    path: str = ""
    source: str = Source.OBSERVADO.value
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TimerInfo:
    """Timer systemd usuario observado."""

    name: str
    active: bool
    next_run: str = ""
    last_run: str = ""
    result: str = ""
    source: str = Source.OBSERVADO.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ServiceStatus:
    """Salud del servicio OpenCode (vista limitada y segura)."""

    active: bool
    url: str = ""
    pid: int = 0
    version: str = ""
    exit_code: int = 0
    detail: str = ""
    source: str = Source.OBSERVADO.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Flow:
    """Flujo de trabajo declarado (nombre y descripcion)."""

    name: str
    title: str
    description: str = ""
    steps: list[str] = field(default_factory=list)
    source: str = Source.DECLARADO.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Health:
    """Salud general del plano de control."""

    ok: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    open_code_active: bool = False
    timers_active: int = 0
    timers_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Snapshot:
    """Salida JSON canonica del plano de control local."""

    version: str = "0.1.0"
    generated_at: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    components: list[Component] = field(default_factory=list)
    timers: list[TimerInfo] = field(default_factory=list)
    flows: list[Flow] = field(default_factory=list)
    health: Health = field(default_factory=Health)
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["components"] = [c.to_dict() for c in self.components]
        d["timers"] = [t.to_dict() for t in self.timers]
        d["flows"] = [f.to_dict() for f in self.flows]
        return d
