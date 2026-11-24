#!/usr/bin/env bash
# Uso: printf '%s' "$SECRET_KEY" | bash desplegar.sh <tag>
# Lee SECRET_KEY de stdin, guarda la version actual como anterior y
# reemplaza el contenedor por calculadora:<tag>.
set -euo pipefail

CALC_DIR="${CALC_DIR:-/home/ec2-user/calculadora}"
DOCKER="${DOCKER:-docker}"

if [ $# -ne 1 ] || [ -z "$1" ]; then
    echo "Uso: desplegar.sh <tag>" >&2
    exit 2
fi
TAG="$1"

# El secreto llega por stdin: nunca se imprime ni va en la linea de comandos.
SECRET_KEY="$(cat)"
if [ -z "$SECRET_KEY" ]; then
    echo "Falta SECRET_KEY por stdin" >&2
    exit 2
fi

mkdir -p "$CALC_DIR"
ENV_FILE="$CALC_DIR/calculadora.env"
( umask 077; printf 'SECRET_KEY=%s\n' "$SECRET_KEY" > "$ENV_FILE" )
chmod 600 "$ENV_FILE"
unset SECRET_KEY

# $DOCKER sin comillas a proposito: las pruebas lo cambian por "bash docker_falso.sh".
if $DOCKER image inspect calculadora:actual > /dev/null 2>&1; then
    $DOCKER tag calculadora:actual calculadora:anterior
fi

$DOCKER tag "calculadora:$TAG" calculadora:actual

# Mismas opciones que rollback.sh
$DOCKER rm -f calculadora > /dev/null 2>&1 || true
$DOCKER run -d --name calculadora --restart unless-stopped \
    -p 80:8000 -v calculadora-datos:/app/instance \
    --env-file "$ENV_FILE" calculadora:actual > /dev/null

echo "Desplegada calculadora:$TAG"
