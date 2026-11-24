# Calculadora de pasajes · Grupo 4 (Lenguajes de programación y QA)

Aplicación web en **Python + Flask** que calcula cuánto gasta un estudiante al
mes en bus en Quito ($0.35 hasta el 31/12/2026 y $0.40 desde el 01/01/2027).
Cada estudiante crea su cuenta, calcula su gasto y lo ve guardado en su historial.

Es el ejemplo común del grupo: cada integrante trabaja una etapa de calidad
sobre este mismo código.

## Qué hace

- **Registro e inicio de sesión** con Flask-Login. Las contraseñas se guardan
  con hash (`werkzeug.security`), nunca en texto plano.
- **Base de datos SQLite** con Flask-SQLAlchemy: tablas `Usuario` y `Calculo`.
- **Historial**: cada usuario ve solo sus cálculos (fecha, viajes, días, total).
- **Validación**: viajes y días deben ser enteros no negativos y los días van
  de 0 a 31. Los errores se muestran en la página.
- **Detalle del cálculo**: pasajes del mes (viajes x días), tarifa aplicada y total.
- **Comparación 2026 vs 2027**: cuánto más gastaría con la tarifa nueva ($0.40)
  con los mismos viajes y días.
- **Resumen del historial**: número de cálculos y total acumulado, y un botón
  para eliminar cada cálculo (formulario POST con confirmación).

### Interfaz

- Estilo oscuro y azul con colores en variables CSS (`:root` en `style.css`).
- Responsive: en el celular el menú se centra, el formulario va en una columna
  y la tabla del historial se ve como tarjetas.
- El formulario conserva lo escrito y la fecha viene con la de hoy.
- Ícono de pestaña (`static/favicon.svg`).
- Avisos de color: verde para éxito, azul para información y rojo para errores.
- El único JavaScript es el `confirm()` antes de eliminar un cálculo.

### Rutas

| Ruta | Método | Qué hace |
|------|--------|----------|
| `/registro` | GET, POST | Crear cuenta |
| `/login` | GET, POST | Iniciar sesión |
| `/logout` | GET | Cerrar sesión |
| `/` | GET, POST | Calculadora (pide sesión) |
| `/historial` | GET | Historial con resumen (pide sesión) |
| `/historial/<id>/eliminar` | POST | Borra un cálculo propio (pide sesión) |

## Los 3 errores intencionales

| # | Error intencional | Dónde está | Lo detecta |
|---|-------------------|-----------|------------|
| 1 | Contraseña escrita en el código | `app/config.py` | SonarQube |
| 2 | Usa `>` en vez de `>=`: el 1/1/2027 todavía cobra $0.35 | `app/tarifas.py` | pytest |
| 3 | Viajes y días llegan como texto y no se convierten a número | `app/rutas.py` | Playwright |

Cada error tiene un comentario en el código con su corrección.
**No los corrijan en la rama principal**: la demo consiste en mostrarlos en
rojo y corregirlos en vivo.

## Estructura

```
calculadora-pasajes/
├── app/
│   ├── __init__.py        # create_app(): arma la app, conecta extensiones y blueprints
│   ├── config.py          # configuración (error 1)
│   ├── extensiones.py     # db (SQLAlchemy) y login_manager (Flask-Login)
│   ├── modelos.py         # tablas Usuario y Calculo
│   ├── tarifas.py         # lógica de negocio, sin Flask (error 2): tarifa, gasto,
│   │                      #   pasajes del mes, comparación 2026 vs 2027
│   ├── validacion.py      # validación de formularios, sin Flask
│   ├── auth.py            # blueprint "auth": registro, login, logout
│   ├── rutas.py           # blueprint "calculadora": cálculo, historial y eliminar (error 3)
│   ├── templates/         # base.html + páginas que la extienden
│   └── static/            # style.css y favicon.svg
├── tests/
│   ├── conftest.py        # levanta la app con una base de datos temporal
│   ├── unitarias/         # PERSONA 1 · pytest
│   └── e2e/               # PERSONA 3 · Playwright
├── sonar-project.properties   # PERSONA 2 · SonarQube Cloud
├── Jenkinsfile                # PERSONA 4 · Jenkins
├── requirements.txt
└── run.py
```

La base de datos real se crea sola en `instance/calculadora.db` la primera vez
que se arranca la app. Las pruebas usan otra base temporal y no la tocan.

## Quién hace qué

| Persona | Parte | Archivos |
|---------|-------|----------|
| 1 | Lenguaje y pruebas unitarias | `tests/unitarias/` |
| 2 | SonarQube Cloud | `sonar-project.properties` |
| 3 | Selenium / Playwright | `tests/e2e/` |
| 4 | Jenkins | `Jenkinsfile` |

Cada uno trabaja en **su propia rama** y sube sus cambios con un pull request.

## Cómo ejecutarlo

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python run.py          # abre http://localhost:5000 (primero regístrate)
pytest                 # corre todas las pruebas
```

## Qué debe salir en las pruebas

Con los errores intencionales, `pytest` muestra **3 pruebas en rojo**:

| Prueba | Archivo | Por qué falla |
|--------|---------|---------------|
| `test_tarifa_desde_el_1_de_enero_de_2027_es_40_centavos` | `tests/unitarias/test_tarifas.py` | error 2 |
| `test_estudiante_calcula_su_gasto_mensual` | `tests/e2e/test_calculadora.py` | error 3 |
| `test_el_calculo_aparece_en_el_historial_y_se_puede_eliminar` | `tests/e2e/test_calculadora.py` | error 3 (el cálculo nunca se guarda) |

Al corregir los errores 2 y 3, todo queda en verde (20 pruebas).
Con el error 3 se ve la página "Internal Server Error" de Flask: a propósito
no hay una página de error personalizada, para que en la demo se vea el 500. El error 1 no lo detecta
pytest: lo marca SonarCloud como vulnerabilidad (regla `python:S2068`, "Credentials should not be hard-coded").

## Comandos útiles

```bash
pytest tests/unitarias --cov=app --cov-report=xml   # pruebas + cobertura para Sonar
pytest tests/e2e --headed                           # ver el navegador mientras prueba
playwright codegen http://localhost:5000            # grabar una prueba haciendo clics
```
