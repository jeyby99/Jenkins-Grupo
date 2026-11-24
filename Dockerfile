# Imagen de produccion de la calculadora
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Usuario sin privilegios
RUN useradd --create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY requirements-app.txt .
RUN pip install -r requirements-app.txt

# Solo el codigo de la app
COPY app/ app/
COPY run.py .

# Carpeta de la base SQLite (se monta como volumen)
RUN mkdir -p /app/instance && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/login', timeout=3)"

# Un solo proceso: create_all con SQLite y varios procesos puede chocar
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "app:create_app()"]
