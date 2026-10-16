"""Verdad declarada: flujos sin hook inventado, cierre visible, salud acotada.

Regresiones de T1 de odd/tasks/panel-verdad-declarado.md:
- ningun flujo declarado promete un hook `pre-commit` (no existe en el repo);
- existe un flujo declarado `cierre` que nombra `./verify.sh`;
- `verify.sh` (raiz del repo) se observa como componente de kind script;
- la etiqueta de salud del panel dice que mide runtime, no el cierre completo.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from control import collect
from control.model import ComponentKind, ServiceStatus, Source

INDEX = Path(__file__).resolve().parent.parent / "web" / "index.html"
README = Path(__file__).resolve().parent.parent / "README.md"


def health_pill_lines(html: str) -> list[str]:
    """Bloque de asignacion que pinta la etiqueta de salud (health-pill) en el JS."""
    return [
        m.group(0)
        for m in re.finditer(r"health-pill'\)\.innerHTML\s*=.*?;", html, re.S)
    ]


class TestFlujosDeclarados(unittest.TestCase):
    def setUp(self) -> None:
        self.flows = collect._build_flows()  # noqa: SLF001 - contrato de flujos declarados

    def test_ningun_flujo_promete_pre_commit(self) -> None:
        for f in self.flows:
            texto = " ".join([f.name, f.title, f.description, *f.steps])
            self.assertNotIn("pre-commit", texto, f"flujo {f.name} promete un hook inexistente")

    def test_existe_flujo_cierre_declarado(self) -> None:
        cierre = [f for f in self.flows if f.name == "cierre"]
        self.assertEqual(len(cierre), 1, "falta el flujo declarado 'cierre'")
        self.assertEqual(cierre[0].source, Source.DECLARADO.value)
        self.assertIn("verify.sh", cierre[0].description)

    def test_flujo_cierre_nombra_los_checks_reales(self) -> None:
        cierre = next(f for f in self.flows if f.name == "cierre")
        for token in ("unittest", "skills", "drift", "qa-gate"):
            self.assertIn(token, cierre.description, f"cierre no nombra {token}")

    def test_qa_gate_conserva_id_y_no_promete_hook(self) -> None:
        gate = [f for f in self.flows if f.name == "qa-gate"]
        self.assertEqual(len(gate), 1, "el id 'qa-gate' debe conservarse")
        self.assertEqual(gate[0].source, Source.DECLARADO.value)


class TestVerifyShObservado(unittest.TestCase):
    def test_collect_root_entrypoints_detecta_verify(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "verify.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            found = collect._collect_root_entrypoints(root)  # noqa: SLF001
            nombres = {(c.name, c.kind, c.source) for c in found}
            self.assertIn(
                ("verify", ComponentKind.SCRIPT.value, Source.OBSERVADO.value), nombres
            )

    def test_collect_root_entrypoints_ausente_no_falla(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(collect._collect_root_entrypoints(Path(td)), [])  # noqa: SLF001

    def test_verify_sh_en_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "verify.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            with mock.patch.object(
                collect, "_opencode_service", return_value=ServiceStatus(active=True)
            ), mock.patch.object(collect, "_systemd_timers", return_value=[]):
                snap = collect.collect_snapshot(root)
            self.assertTrue(
                any(c.path.endswith("verify.sh") for c in snap.components),
                "verify.sh no aparece como componente observado",
            )


class TestSubagentesDeclarados(unittest.TestCase):
    """El parser no debe confundir el bloque 'agents' con su primer hijo."""

    def test_nombra_los_subagentes_reales(self) -> None:
        eco = Path(__file__).resolve().parent.parent.parent
        subs = collect._parse_opencode_subagents(eco)  # noqa: SLF001
        nombres = {c.name for c in subs}
        self.assertNotIn("agents", nombres, "el contenedor no es un subagente")
        self.assertEqual(nombres, {"odd-worker", "odd-verifier"})

    def test_no_cruza_llaves_anidadas(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "configs"
            cfg.mkdir()
            (cfg / "opencode.jsonc").write_text(
                '{"agents": {'
                '"a-uno": {"mode": "subagent", "description": "primero"},'
                '"b-dos": {"mode": "subagent", "hidden": true, "description": "segundo"}'
                "}}",
                encoding="utf-8",
            )
            subs = collect._parse_opencode_subagents(root)  # noqa: SLF001
            self.assertEqual([c.name for c in subs], ["a-uno", "b-dos"])


class TestEtiquetaSaludAcotada(unittest.TestCase):
    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")

    def test_health_pill_no_dice_sano_a_secas(self) -> None:
        lineas = health_pill_lines(self.html)
        self.assertTrue(lineas, "no se encuentra la pintura de health-pill")
        visible = " ".join(lineas)
        for suelta in ("</span>sano<", "</span>revisar<"):
            self.assertNotIn(
                suelta, visible, "la etiqueta debe acotar su alcance, no decir 'sano' a secas"
            )
        self.assertIn("runtime sano", visible)
        self.assertIn("runtime: revisar", visible)

    def test_health_pill_explica_el_alcance(self) -> None:
        marca = re.search(r'<span[^>]*id="health-pill"[^>]*>', self.html)
        self.assertIsNotNone(marca, "no existe el contenedor health-pill")
        # Anclado al propio elemento: una ventana de contexto incluiria el markup
        # de los botones vecinos y la asercion pasaria aunque falte la explica.
        atributos = re.findall(r'(?:title|aria-label)="([^"]*)"', marca.group(0))
        self.assertTrue(
            atributos,
            "health-pill debe explicar su alcance en title/aria-label propios",
        )
        self.assertRegex(
            " ".join(atributos),
            r"verify\.sh|tests",
            "el alcance debe citar que no cubre el cierre",
        )


class TestReadmeDeclaraCierre(unittest.TestCase):
    def test_readme_lista_flujo_cierre(self) -> None:
        texto = README.read_text(encoding="utf-8")
        linea = next(
            (ln for ln in texto.splitlines() if "flujos declarados" in ln.lower()), ""
        )
        self.assertTrue(linea, "el README ya no lista los flujos declarados")
        self.assertIn("cierre", linea.lower())

    def test_readme_acota_el_alcance_de_salud(self) -> None:
        texto = README.read_text(encoding="utf-8")
        aclaracion = next(
            (
                ln
                for ln in texto.splitlines()
                if "verify.sh" in ln and "salud" in ln.lower() and not ln.strip().startswith("#")
            ),
            "",
        )
        self.assertTrue(aclaracion, "el README debe aclarar el alcance de la salud")


if __name__ == "__main__":
    unittest.main()