"""Revisa en SonarCloud si hay credenciales escritas en el código.

El Quality Gate solo mira el código nuevo, así que esta revisión consulta
las vulnerabilidades abiertas del proyecto y falla si encuentra alguna
regla de credenciales (python:S2068 o secrets:*) dentro de la carpeta app/.

Salida: 0 sin hallazgos, 1 con hallazgos, 2 si no se pudo consultar SonarCloud.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

URL = "https://sonarcloud.io/api/issues/search"
TAMANO_PAGINA = 500


class ErrorSonar(Exception):
    """No se pudo consultar SonarCloud."""


def _es_secreto(regla: str) -> bool:
    return regla == "python:S2068" or regla.startswith("secrets:")


def secretos_abiertos(respuesta: dict, carpeta: str = "app/") -> list[str]:
    hallazgos = []
    for i in respuesta.get("issues", []):
        regla = i.get("rule", "")
        ruta = i.get("component", "").split(":", 1)[-1]
        if _es_secreto(regla) and ruta.startswith(carpeta):
            hallazgos.append(f"{ruta}:{i.get('line', '?')} {regla} {i.get('message', '')}")
    return hallazgos


def _pedir(url: str, token: str | None) -> dict:
    peticion = urllib.request.Request(url)
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(peticion, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise ErrorSonar(f"SonarCloud respondió con error HTTP {e.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ErrorSonar(f"No se pudo consultar SonarCloud: {e}") from None


def obtener_issues(proyecto: str, token: str | None = None) -> dict:
    """Descarga todas las vulnerabilidades abiertas (con paginación)."""
    issues = []
    pagina = 1
    while True:
        consulta = urllib.parse.urlencode({
            "componentKeys": proyecto, "resolved": "false",
            "types": "VULNERABILITY", "ps": TAMANO_PAGINA, "p": pagina,
        })
        datos = _pedir(f"{URL}?{consulta}", token)
        issues.extend(datos.get("issues", []))
        total = datos.get("total", len(issues))
        if not datos.get("issues") or len(issues) >= total:
            return {"issues": issues, "total": total}
        pagina += 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", required=True, help="clave del proyecto en SonarCloud")
    parser.add_argument("--carpeta", default="app/", help="carpeta a revisar (por defecto app/)")
    args = parser.parse_args(argv)

    try:
        respuesta = obtener_issues(args.proyecto, os.environ.get("SONAR_TOKEN") or None)
    except ErrorSonar as e:
        print(e)
        return 2

    hallazgos = secretos_abiertos(respuesta, args.carpeta)
    if hallazgos:
        print("SonarCloud encontró credenciales escritas en el código:")
        for h in hallazgos:
            print(f"  {h}")
        return 1
    print("Sin credenciales escritas en el código.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
