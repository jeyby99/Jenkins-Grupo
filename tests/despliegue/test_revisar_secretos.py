"""Pruebas de ci/revisar_secretos.py (sin red: respuestas de SonarCloud capturadas)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ci"))

import revisar_secretos as rs  # noqa: E402


def issue(regla, ruta, linea, mensaje="msg"):
    return {
        "rule": regla,
        "component": f"jeyby99_Jenkins-Grupo:{ruta}",
        "line": linea,
        "message": mensaje,
    }


def test_respuesta_vacia_no_reporta_nada():
    assert rs.secretos_abiertos({"issues": []}) == []


def test_s2068_en_config_se_reporta_con_archivo_y_linea():
    resp = {"issues": [issue("python:S2068", "app/config.py", 13, "Revoke and change this password.")]}
    assert rs.secretos_abiertos(resp) == [
        "app/config.py:13 python:S2068 Revoke and change this password."
    ]


def test_s4502_se_ignora():
    resp = {"issues": [issue("python:S4502", "app/__init__.py", 11)]}
    assert rs.secretos_abiertos(resp) == []


def test_regla_secrets_se_reporta():
    resp = {"issues": [issue("secrets:S6698", "app/config.py", 20)]}
    assert len(rs.secretos_abiertos(resp)) == 1


def test_s2068_fuera_de_app_se_ignora():
    resp = {"issues": [issue("python:S2068", "tests/x.py", 3)]}
    assert rs.secretos_abiertos(resp) == []


def test_main_sale_1_si_hay_hallazgos(monkeypatch, capsys):
    monkeypatch.setattr(
        rs, "obtener_issues",
        lambda proyecto, token=None: {"issues": [issue("python:S2068", "app/config.py", 13)]},
    )
    assert rs.main(["--proyecto", "p"]) == 1
    salida = capsys.readouterr().out
    assert "credenciales escritas en el código" in salida
    assert "app/config.py:13" in salida


def test_main_sale_0_si_no_hay_hallazgos(monkeypatch, capsys):
    monkeypatch.setattr(rs, "obtener_issues", lambda proyecto, token=None: {"issues": []})
    assert rs.main(["--proyecto", "p"]) == 0
    assert "Sin credenciales escritas en el código." in capsys.readouterr().out


def test_main_sale_2_si_falla_la_red(monkeypatch, capsys):
    def falla(proyecto, token=None):
        raise rs.ErrorSonar("no se pudo consultar SonarCloud")

    monkeypatch.setattr(rs, "obtener_issues", falla)
    assert rs.main(["--proyecto", "p"]) == 2
    assert "no se pudo consultar SonarCloud" in capsys.readouterr().out
