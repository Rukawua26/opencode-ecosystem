"""Smoke test del frontend: el JS del panel debe parsear (node --check)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "web" / "index.html"

ESTADOS_TAREA = ("pending", "running", "waiting", "done", "failed", "dead", "cancelled")
MARCAS_CLI = (
    "python3 -m control.cli doctor",
    "python3 -m control.cli task add",
    "python3 -m control.cli task list",
    "python3 -m control.cli task run",
    "python3 -m control.cli task assess",
    "python3 -m control.cli receipt",
    "python3 -m control.cli reconcile",
    "python3 -m control --once --pretty",
    "./opencode-ecosystem status",
    "./opencode-ecosystem sync --apply",
    "./opencode-ecosystem publish --yes",
)


def inline_scripts(html: str) -> list[str]:
    """Contenido de todos los bloques <script> del panel (head y body)."""
    return re.findall(r"<script>(.*?)</script>", html, re.S)


def panel_view(html: str, view: str) -> str:
    """HTML de la <section class="panel" data-view="view"> (soporta atributos extra)."""
    m = re.search(
        r'<section[^>]*\bdata-view="%s"[^>]*>.*?</section>' % re.escape(view), html, re.S
    )
    return m.group(0) if m else ""


def declared_views(html: str) -> list[str]:
    """Vistas declaradas en la constante VIEWS del script."""
    m = re.search(r"const\s+VIEWS\s*=\s*\[([^\]]*)\]", html)
    if not m:
        return []
    return re.findall(r"['\"]([\w-]+)['\"]", m.group(1))


def static_options(html: str) -> list[tuple[str, str]]:
    """Pares (value, texto) no vacios de cada <option> estatica del markup (sin scripts)."""
    markup = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"<option\b[^>]*>(.*?)</option>", markup, re.S):
        vm = re.search(r'value="([^"]*)"', m.group(0))
        val = (vm.group(1) if vm else "").strip()
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if val or text:
            out.append((val, text))
    return out


class TestFrontendJS(unittest.TestCase):
    def test_inline_script_parses(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node no disponible")
        html = INDEX.read_text(encoding="utf-8")
        scripts = inline_scripts(html)
        self.assertTrue(scripts, "no hay <script> inline en index.html")
        for i, script in enumerate(scripts, 1):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(script)
                tmp = f.name
            res = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"JS roto en bloque {i}:\n{res.stderr}")

    def test_csrf_caducado_tiene_mensaje_de_reanudacion(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("Recarga la página", html)
        self.assertIn("csrfHint", html)

    def test_filtros_de_cola_presentes(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for fid in ("f-status", "f-agent", "f-model", "f-sens",
                    "renderTasks", "taskDuration"):
            self.assertIn(fid, html)
        self.assertIn('value="waiting"', html)
        self.assertIn("waiting:'warn'", html)

    def test_accesibilidad_basica(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn(":focus-visible", html)
        self.assertIn('role="button"', html)
        self.assertIn('aria-live="polite"', html)

    def test_sin_alert_nativo(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for script in inline_scripts(html):
            self.assertNotIn("alert(", script)

    def test_interruptor_de_tema(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for marca in ("data-theme", "panel-theme", "toggleTheme", "isDarkTheme",
                      "paintThemeBtn", 'id="theme-toggle"',
                      'aria-label="cambiar de tema"', ":root[data-theme=",
                      "--tagbg", "--hover", "var(--tagbg)", "var(--hover)"):
            self.assertIn(marca, html)
        self.assertEqual(html.count("/*__CSRF__*/"), 1,
                         "el marcador CSRF debe seguir una sola vez en el script del body")

    def test_favicon_declarado(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn('<link rel="icon" href="data:,">', html)

    def test_mapa_presente(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for marca in ('id="map"', "loadGraph", "/api/graph", "renderGraph",
                      "Mapa operativo"):
            self.assertIn(marca, html)

    def test_monitor_vivo_y_traza_presentes(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for marca in ('id="live-body"', 'id="trace-panel"', "showTrace",
                      "hideTrace", "renderLive", "scheduleTaskPoll",
                      "/api/tasks/'", "/trace"):
            self.assertIn(marca, html)

    def test_modal_accesible(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn('role="dialog"', html)
        self.assertIn('aria-modal="true"', html)
        self.assertIn('aria-labelledby="hist-title"', html)
        self.assertIn("'Escape'", html)
        self.assertIn("histTrigger", html)


class TestVistaAyuda(unittest.TestCase):
    """La vista ❓ Ayuda es un glosario estatico: solo marcas, sin parrafos exactos."""

    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")
        self.section = panel_view(self.html, "ayuda")
        self.assertTrue(self.section, "falta la <section data-view='ayuda'>")

    def test_pestana_de_ayuda_accesible(self) -> None:
        tab = re.search(r"<button[^>]*\bid=\"tab-ayuda\"[^>]*>", self.html)
        self.assertIsNotNone(tab, "falta la pestana #tab-ayuda")
        markup = tab.group(0)
        self.assertIn('role="tab"', markup)
        self.assertIn('aria-selected="false"', markup)
        self.assertIn("showView('ayuda')", markup)

    def test_ayuda_es_una_vista_mas_del_mecanismo_generico(self) -> None:
        views = declared_views(self.html)
        self.assertIn("ayuda", views)
        for view in views:
            self.assertIn('id="tab-%s"' % view, self.html)
            self.assertTrue(panel_view(self.html, view), "sin sección para la vista %r" % view)
        # showView/viewFromLocation siguen siendo genericos: no llevan la lista a mano
        self.assertIn("tab-'+v", self.html)
        self.assertIn("VIEWS.includes(h)", self.html)
        self.assertIn("'panel-view'", self.html)
        # la vista por defecto no cambia
        self.assertIn("return 'resumen';", self.html)

    def test_las_vistas_se_explican(self) -> None:
        for vista in ("Resumen", "En vivo", "Mapa", "Actividad", "Ayuda"):
            self.assertIn(vista, self.section)

    def test_waiting_no_se_presenta_como_ejecucion_activa(self) -> None:
        """Una tarea waiting es decision humana pendiente, no proceso vivo."""
        for token in ("requiere decisión", "esperando decisión desde hace ",
                      "pendiente(s) de decisión humana",
                      "no se están ejecutando"):
            self.assertIn(token, self.html)
        self.assertIn("sin proceso en ejecución", self.html)
        self.assertNotIn("sin ejecución activa — la cola está en reposo", self.html)
        # renderLive separa running de waiting: no cae a waiting como si ejecutara
        script = "".join(inline_scripts(self.html))
        self.assertIn("ALL_TASKS.find(x=>x.status==='running')", script)
        self.assertIn("ALL_TASKS.filter(x=>x.status==='waiting')", script)
        self.assertNotIn(
            "ALL_TASKS.find(x=>x.status==='running') || ALL_TASKS.find(x=>x.status==='waiting')",
            script,
        )

    def test_vista_en_vivo_usa_traza_y_poller_existentes(self) -> None:
        self.assertIn("en-vivo", declared_views(self.html))
        live = panel_view(self.html, "en-vivo")
        for token in ('id="trace-panel"', 'id="trace-body"', 'id="live-body-detail"'):
            self.assertIn(token, live)
        for token in ("/api/execution-metrics", "refreshTrace(selectedTrace)",
                      "showView('en-vivo')", "document.hidden ? 60000 : (active ? 5000 : 30000)"):
            self.assertIn(token, self.html)

    def test_fuentes_de_datos_declaradas(self) -> None:
        for marca in ("127.0.0.1:8765", "systemd", "SQLite", "snapshot",
                      "reconcile.py", "30 días", "20 000"):
            self.assertIn(marca, self.section)

    def test_tabla_de_estados_de_tarea(self) -> None:
        rows = re.findall(r"<tr.*?</tr>", self.section, re.S)
        self.assertTrue(rows, "la tabla de estados no tiene filas")
        for estado in ESTADOS_TAREA:
            self.assertTrue(
                any(estado in row for row in rows),
                "el estado %r no aparece en ninguna fila de la ayuda" % estado,
            )

    def test_badges_y_colores_explicados(self) -> None:
        for marca in ("observado", "declarado", "sano", "aviso", "fallo", "informativo"):
            self.assertIn(marca, self.section)

    def test_limites_y_garantias(self) -> None:
        for marca in ("No relanza trabajo automáticamente", "CSRF", "127.0.0.1",
                      "control/README.md", "odd/tasks/"):
            self.assertIn(marca, self.section)

    def test_comandos_cli_para_lo_que_no_hay_en_el_panel(self) -> None:
        for cmd in MARCAS_CLI:
            self.assertIn(cmd, self.section)

    def test_ayuda_no_expone_datos_sensibles(self) -> None:
        """El glosario no debe rellenar campos prohibidos ni traer peticiones propias."""
        self.assertNotIn("/api/", self.section)
        self.assertNotIn("fetch(", self.section)
        for script in inline_scripts(self.html):
            self.assertNotIn("alert(", script)


class TestColumnaPorQue(unittest.TestCase):
    """La columna «¿Por que tiene este resultado?» del panel de traza: solo marcas."""

    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")

    def test_marcas_estructurales(self) -> None:
        for marca in ('id="trace-why"', "explainTrace",
                      "¿Por qué tiene este resultado?",
                      "no hay información suficiente"):
            self.assertIn(marca, self.html)

    def test_bloque_error_registrado_y_que_revisar(self) -> None:
        for marca in ("Error registrado", "Qué revisar",
                      "sin mensaje de error registrado"):
            self.assertIn(marca, self.html)


class TestAntiDriftAyuda(unittest.TestCase):
    """Cada opcion de cada desplegable debe estar documentada en la vista Ayuda."""

    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")
        self.section = panel_view(self.html, "ayuda")
        self.assertTrue(self.section, "falta la <section data-view='ayuda'>")
        self.texto = re.sub(r"<[^>]+>", " ", self.section)

    def opciones_agente_js(self) -> list[str]:
        m = re.search(r"//\s*select de agentes permitidos.*?(\[[^\]]*\])", self.html, re.S)
        self.assertIsNotNone(m, "no se encontro la lista JS de agentes permitidos")
        agentes = re.findall(r"'([\w-]+)'", m.group(1))
        self.assertTrue(agentes, "la lista JS de agentes esta vacia")
        return agentes

    def test_agentes_del_select_js_documentados(self) -> None:
        for agente in self.opciones_agente_js():
            self.assertIn(agente, self.texto, "opcion sin documentar en Ayuda: %s" % agente)

    def test_opciones_estaticas_documentadas(self) -> None:
        opciones = static_options(self.html)
        self.assertTrue(opciones, "no hay <option> estaticas en index.html")
        for val, text in opciones:
            documentado = (val and val in self.texto) or (text and text in self.texto)
            self.assertTrue(documentado,
                            "opcion sin documentar en Ayuda: %s" % (val or text))


if __name__ == "__main__":
    unittest.main()
