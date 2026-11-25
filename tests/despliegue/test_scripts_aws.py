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
            "DOCKER_IDS": (tmp_path / "ids.txt").as_posix(),
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


def crear_env(carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "calculadora.env").write_text("SECRET_KEY=x\n")


def lineas(log):
    return log.read_text().splitlines()


def test_primer_despliegue_sin_actual(entorno):
    env, log, imagenes, carpeta = entorno
    poner_imagenes(imagenes, ["calculadora:abc-1"])
    r = ejecutar("desplegar.sh", env, ["abc-1"], "clave")
    assert r.returncode == 0, r.stderr
    texto = log.read_text()
    assert "tag calculadora:actual calculadora:anterior" not in texto
    run = [l for l in lineas(log) if l.startswith("run")]
    assert run
    assert "-p 8090:8000" in run[0]
    assert "--memory 192m" in run[0]
    assert f"--env-file {(carpeta / 'calculadora.env').as_posix()}" in run[0]
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
    assert "clave-super-secreta" not in log.read_text()
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
    env, log, imagenes, carpeta = entorno
    poner_imagenes(imagenes, ["calculadora:anterior"])
    crear_env(carpeta)
    r = ejecutar("rollback.sh", env)
    assert r.returncode == 0, r.stderr
    ls = lineas(log)
    etiqueta = ls.index("tag calculadora:anterior calculadora:actual")
    run = [i for i, l in enumerate(ls) if l.startswith("run") and "calculadora:actual" in l]
    assert run and run[0] > etiqueta


def test_falla_el_run_y_se_restaura_la_anterior(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:actual", "calculadora:abc-3"])
    env["DOCKER_FALLAR_RUN"] = "calculadora:abc-3"
    r = ejecutar("desplegar.sh", env, ["abc-3"], "clave")
    assert r.returncode != 0
    assert "Se restauró la versión anterior" in r.stdout + r.stderr
    ls = lineas(log)
    fallido = [i for i, l in enumerate(ls) if l.startswith("run") and "calculadora:abc-3" in l]
    assert fallido
    despues = ls[fallido[0] + 1:]
    assert "tag calculadora:anterior calculadora:actual" in despues
    assert any(l.startswith("run") and "calculadora:actual" in l for l in despues)


def test_falla_el_run_sin_anterior_sale_con_error(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:abc-3"])
    env["DOCKER_FALLAR_RUN"] = "calculadora:abc-3"
    r = ejecutar("desplegar.sh", env, ["abc-3"], "clave")
    assert r.returncode != 0
    assert "no hay versión anterior" in (r.stdout + r.stderr).lower()


def test_rollback_se_niega_si_anterior_es_la_misma_que_actual(entorno):
    env, log, imagenes, carpeta = entorno
    poner_imagenes(imagenes, ["calculadora:actual", "calculadora:anterior"])
    (carpeta.parent / "ids.txt").write_text("calculadora:actual sha-1\ncalculadora:anterior sha-1\n")
    crear_env(carpeta)
    r = ejecutar("rollback.sh", env)
    assert r.returncode == 1
    assert "Ya se está usando la versión anterior" in r.stdout + r.stderr
    assert not any(l.startswith("run") for l in lineas(log))


def test_rollback_sin_archivo_env_falla_sin_tocar_el_contenedor(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:anterior"])
    r = ejecutar("rollback.sh", env)
    assert r.returncode == 1
    assert "calculadora.env" in r.stdout + r.stderr
    assert not any(l.startswith(("rm", "run")) for l in lineas(log))


def test_el_puerto_se_puede_cambiar(entorno):
    env, log, imagenes, _ = entorno
    poner_imagenes(imagenes, ["calculadora:abc-9"])
    env["PUERTO"] = "8095"
    r = ejecutar("desplegar.sh", env, ["abc-9"], "clave")
    assert r.returncode == 0, r.stderr
    run = [l for l in lineas(log) if l.startswith("run")]
    assert "-p 8095:8000" in run[0]
