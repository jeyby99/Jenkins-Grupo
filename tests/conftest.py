"""Configuración compartida de las pruebas.

El fixture `url_base` levanta la calculadora en un hilo aparte (en un puerto libre que elige el sistema)
para que las pruebas de navegador tengan una página real que abrir.
Así no hace falta ejecutar `python run.py` antes de las pruebas,
y Jenkins puede correr todo con un solo comando.

La app de pruebas usa una base de datos temporal (en una carpeta que crea
pytest), así nunca toca la base real de instance/calculadora.db.
"""

import threading

import pytest
from werkzeug.serving import make_server

from app import create_app


@pytest.fixture(scope="session")
def url_base(tmp_path_factory):
    ruta_bd = tmp_path_factory.mktemp("bd") / "pruebas.db"
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta_bd.as_posix()}",
    })

    servidor = make_server("127.0.0.1", 0, app, threaded=True)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_port}"
    servidor.shutdown()
