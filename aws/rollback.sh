#!/usr/bin/env bash
# Uso: bash rollback.sh
# Vuelve a calculadora:anterior y recrea el contenedor.
set -euo pipefail

CALC_DIR="${CALC_DIR:-/home/ec2-user/calculadora}"
DOCKER="${DOCKER:-docker}"
ENV_FILE="$CALC_DIR/calculadora.env"

# $DOCKER sin comillas a proposito: las pruebas lo cambian por "bash docker_falso.sh".
if ! $DOCKER image inspect calculadora:anterior > /dev/null 2>&1; then
    echo "No hay versión anterior para volver"
    exit 1
fi

$DOCKER tag calculadora:anterior calculadora:actual

# Mismas opciones que desplegar.sh
$DOCKER rm -f calculadora > /dev/null 2>&1 || true
$DOCKER run -d --name calculadora --restart unless-stopped \
    -p 80:8000 -v calculadora-datos:/app/instance \
    --env-file "$ENV_FILE" calculadora:actual > /dev/null

echo "Vuelta a la versión anterior"
