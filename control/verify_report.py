"""Lectura saneada del informe privado del cierre (`verify.sh`).

Reglas de este modulo:
- Nunca lanza: un informe ausente, corrupto o de otro esquema se devuelve como
  estado desconocido, no como error.
- Allowlist estricta de campos. Cualquier clave extra del fichero se descarta.
- Todo texto pasa por un saneador: sin caracteres de control, longitud acotada.
- NO inventa causas. Solo traduce literales conocidos de `verify.sh`; para
  cualquier otro detalle dice explicitamente que no hay causa disponible.
- No lee stdout/stderr de los hijos: no estan en el informe y no se piden.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path


REPORT_PATH = Path.home() / ".local" / "share" / "opencode-control" / "verify-last.json"

SCHEMA = 1
# Un informe mas viejo que esto se marca como antiguo: describe el pasado, no
# el estado actual, aunque su exit_code sea 0.
FRESH_S = 6 * 3600
# "en curso" mas viejo que esto significa que verify.sh murio: se marca
# interrumpido, nunca completado.
RUNNING_STALE_S = 900

MAX_CHECKS = 64
MAX_TEXT = 200

_ALLOWED_CHECK_KEYS = ("name", "scope", "result", "detail", "rc", "elapsed_s")
_KNOWN_RESULTS = frozenset({"ok", "warn", "fail", "unavailable", "incomplete"})
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Secuencias ANSI completas: si solo se quita el ESC, quedan restos legibles
# ("[2J") que no son texto del informe.
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _text(value: object, limit: int = MAX_TEXT) -> str:
    """Texto plano, sin secuencias ANSI ni caracteres de control, y acotado."""
    if not isinstance(value, str):
        return ""
    return _CONTROL.sub("", _ANSI.sub("", value)).strip()[:limit]


def _rc(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return ""
    return _text(str(value), 8)


def _int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _age_s(raw: object) -> float | None:
    """Antiguedad en segundos a partir del ISO de `verify.sh` (offset numerico)."""
    text = _text(raw, 40)
    match = re.match(
        r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{4})$", text
    )
    if not match:
        return None
    year, month, day, hour, minute, second, offset = match.groups()
    sign = 1 if offset[0] == "+" else -1
    shift = sign * (int(offset[1:3]) * 3600 + int(offset[3:5]) * 60)
    try:
        import calendar
        stamp = calendar.timegm(
            (int(year), int(month), int(day), int(hour), int(minute), int(second), 0, 0, 0)
        ) - shift
    except (ValueError, OverflowError):
        return None
    return max(0.0, round(time.time() - stamp, 1))


# Traduccion de los literales FIJOS que produce verify.sh. Si el detalle no
# esta aqui, no se explica: se dice que no hay causa disponible.
_EXPLAIN: dict[str, str] = {
    "rc=0": "termino correctamente (rc=0)",
    "aplicable": "habia cambios staged que revisar",
    "no aplicable (sin cambios staged)": (
        "no habia cambios staged, asi que el analisis del staged no aplicaba; "
        "las rutas sensibles rastreadas si se comprobaron"
    ),
    "trigger informativo; rc=1": (
        "aviso informativo de higiene (por ejemplo backups podables). "
        "No es un fallo y no bloquea el cierre"
    ),
    "comando o recurso no disponible": (
        "falta el comando o el recurso que este check necesita; no llego a ejecutarse"
    ),
    "limite de tiempo o terminacion; sin cierre completo": (
        "el check supero su presupuesto de tiempo y fue detenido: "
        "el resultado no es completo"
    ),
    "error operativo o alcance incompleto; rc=2": (
        "el check no pudo completar por error operativo o por un alcance que "
        "el catalogo textual no cubre (por ejemplo un binario en staging)"
    ),
}

_EXPLAIN_LIMITED = (
    "el comando termino con error. El informe guarda solo el codigo de salida, "
    "no la salida del comando, asi que la causa concreta hay que obtenerla "
    "ejecutando ese check en la terminal"
)


def _explain(detail: str, result: str) -> str:
    if detail in _EXPLAIN:
        return _EXPLAIN[detail]
    if result in ("fail", "unavailable", "incomplete"):
        return _EXPLAIN_LIMITED
    return ""


def _empty(state: str, note: str) -> dict:
    return {
        "available": False, "state": state, "age_s": None, "stale": False,
        "started_at": "", "ended_at": "", "elapsed_s": None, "exit_code": None,
        "overall": "unknown", "checks": [], "summary": {}, "failing": [],
        "why": note, "note": note,
    }


def read_report(path: Path | None = None) -> dict:
    """Devuelve el informe saneado. Nunca lanza."""
    target = Path(path) if path else REPORT_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty("none", "sin ejecucion registrada: nunca se ha escrito un informe del cierre")
    except (OSError, ValueError, RecursionError, MemoryError):
        return _empty("corrupt", "informe ilegible o corrupto: no se puede usar como evidencia")
    if not isinstance(raw, dict):
        return _empty("corrupt", "informe con formato inesperado")
    if raw.get("schema") != SCHEMA:
        return _empty("unknown_schema", "informe de otra version de esquema; no se interpreta")

    state = _text(raw.get("state"), 16)
    checks: list[dict] = []
    for item in raw.get("checks") or []:
        if not isinstance(item, dict) or len(checks) >= MAX_CHECKS:
            continue
        result = _text(item.get("result"), 16)
        if result not in _KNOWN_RESULTS:
            continue
        detail = _text(item.get("detail"))
        checks.append({
            "name": _text(item.get("name"), 60),
            "scope": _text(item.get("scope"), 120),
            "result": result,
            "detail": detail,
            "rc": _rc(item.get("rc")),
            "elapsed_s": _int(item.get("elapsed_s")),
            "why": _explain(detail, result),
        })

    age = _age_s(raw.get("ended_at")) if state == "completed" else _age_s(raw.get("started_at"))
    summary: dict[str, int] = {}
    for check in checks:
        summary[check["result"]] = summary.get(check["result"], 0) + 1
    failing = [c["name"] for c in checks if c["result"] != "ok" and c["result"] != "warn"]

    if state == "completed":
        exit_code = _int(raw.get("exit_code"))
        # Sin checks registrados no hay evidencia: exit_code=0 NO es verde.
        # Puede ocurrir si verify.sh introduce un resultado nuevo que aqui no se
        # reconoce y todos los checks se descartan.
        if not checks:
            overall = "unknown"
            why = ("el informe declara una ejecucion completada pero no registro "
                   "ningun check: no hay evidencia para afirmarla")
        elif exit_code == 0:
            overall = "ok"
            why = ""
        elif exit_code is not None:
            overall = "red"
            why = (
                "comprobaciones con resultado bloqueante: " + ", ".join(failing)
                if failing else "el informe declara fallo sin identificar ningun check"
            )
        else:
            overall = "unknown"
            why = "el informe no declara el codigo de salida: no se puede afirmar"
    elif state == "running":
        overall = "unknown"
        why = ("hay un cierre registrado como en curso"
               + (f" desde hace {int(age)} s" if age is not None else ""))
        if age is not None and age > RUNNING_STALE_S:
            state = "interrupted"
            why = ("el cierre empezo pero no dejo resultado final: se quedo "
                   "interrumpido. El marcador de 'en curso' sustituyo al informe "
                   "anterior, asi que no hay un cierre completo que consultar")
    else:
        overall = "unknown"
        why = "estado del informe desconocido"

    # Sin edad legible no se puede afirmar que el dato sea actual.
    stale = bool(age is None or age > FRESH_S)
    if age is None and state == "completed":
        why = (why + " · " if why else "") + (
            "el informe no tiene una fecha utilizable: se trata como antiguo "
            "porque no se puede saber cuando se ejecuto")
    elif stale and overall == "ok":
        why = ("el ultimo cierre completo fue verde, pero es antiguo "
               f"({int(age)} s). Describe el pasado, no el estado actual")

    return {
        "available": True,
        "state": state,
        "age_s": age,
        "stale": stale,
        "started_at": _text(raw.get("started_at"), 40),
        "ended_at": _text(raw.get("ended_at"), 40),
        "elapsed_s": _int(raw.get("elapsed_s")),
        "exit_code": _int(raw.get("exit_code")),
        "overall": overall,
        "checks": checks,
        "summary": summary,
        "failing": failing,
        "why": why,
        "note": (
            "El informe guarda resultado y codigo de salida por check, no la "
            "salida de los comandos. Un cierre verde no cubre sesiones "
            "interactivas ni codigo sin stage."
        ),
    }