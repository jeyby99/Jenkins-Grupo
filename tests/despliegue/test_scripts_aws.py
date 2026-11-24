"""Pruebas de desplegar.sh y rollback.sh con un docker falso."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
AWS = RAIZ / "aws"
FALSO = Path(__file__).resolve().parent / "docker_falso.sh"


@pytest.fixture
def entorno(tmp_path):
    if shutil.which("bash") is None:
        pytest.skip("No hay bash en este equipo")
    log = tmp_path / "docker.log"
    imagenes = tmp_path / "imagenes.txt"
    log.write_text("")
    imagenes.write_text("")
    carpeta = tmp_path / "calculadora"
    env = dict(os.environ)
    env.update(
        {
            "CALC_DIR": carpeta.as_posix(),
            "DOCKER": f"bash {FALSO.as_posix()}",
            "DOCKER_LOG": log.as_posix(),
            "DOCKER_IMAGENES": imagenes.as_posix(),
        }
    )
    return env, log, imagenes, carpeta


def poner_imagenes(imagenes, lista):
    imagenes.write_text("".join(f"{i}\n" for i in lista))


def ejecutar(script, env, args=(), entrada=""):
    return subprocess.run(
        ["bash", (AWS / script).as_posix(), *args],
        input=entrada,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def lineas(log):
    return log.read_text().splitlines()


def test_primer_despliegue_sin_actual(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:abc-1"])
    r = ejecutar("desplegar.sh", env, ["abc-1"], "clave")
    assert r.returncode == 0, r.stderr
    texto = log.read_text()
    assert "tag calculadora:actual calculadora:anterior" not in texto
    run = [l for l in lineas(log) if l.startswith("run")]
    assert run
    assert "-p 80:8000" in run[0]
    assert "calculadora-datos:/app/instance" in run[0]


def test_despliegue_guarda_la_anterior(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:actual", "calculadora:abc-2"])
    r = ejecutar("desplegar.sh", env, ["abc-2"], "clave")
    assert r.returncode == 0, r.stderr
    ls = lineas(log)
    guardar = ls.index("tag calculadora:actual calculadora:anterior")
    nueva = ls.index("tag calculadora:abc-2 calculadora:actual")
    assert guardar < nueva


def test_secreto_no_sale_en_la_salida(entorno):
    env, log, imagenes, carpeta = entorno
    poner_imagenes(imagenes, ["calculadora:abc-1"])
    r = ejecutar("desplegar.sh", env, ["abc-1"], "clave-super-secreta")
    assert r.returncode == 0, r.stderr
    assert "clave-super-secreta" not in r.stdout
    assert "clave-super-secreta" not in r.stderr
    archivo = carpeta / "calculadora.env"
    assert "SECRET_KEY=clave-super-secreta" in archivo.read_text()
    if os.name != "nt":
        assert (archivo.stat().st_mode & 0o777) == 0o600


def test_rollback_sin_anterior_falla(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, [])
    r = ejecutar("rollback.sh", env)
    assert r.returncode == 1
    assert "No hay versión anterior para volver" in r.stdout + r.stderr


def test_rollback_vuelve_a_la_anterior(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:anterior"])
    r = ejecutar("rollback.sh", env)
    assert r.returncode == 0, r.stderr
    ls = lineas(log)
    etiqueta = ls.index("tag calculadora:anterior calculadora:actual")
    run = [i for i, l in enumerate(ls) if l.startswith("run") and "calculadora:actual" in l]
    assert run and run[0] > etiqueta
