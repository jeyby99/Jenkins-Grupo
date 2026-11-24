#!/usr/bin/env bash
# Uso: printf '%s' "$SECRET_KEY" | bash desplegar.sh <tag>
# Lee SECRET_KEY de stdin, guarda la version actual como anterior y
# reemplaza el contenedor por calculadora:<tag>.
#
# Contrato: si el contenedor nuevo no arranca, este script vuelve a levantar
# la version anterior (si existia antes de este despliegue), avisa y sale con
# codigo distinto de 0. rollback.sh carga este archivo (source) para usar la
# misma funcion reemplazar_contenedor; ambos se copian a la misma carpeta.
set -euo pipefail

CALC_DIR="${CALC_DIR:-/home/ec2-user/calculadora}"
DOCKER="${DOCKER:-docker}"

# Unica definicion de las opciones del contenedor. Uso: reemplazar_contenedor <imagen>
# $DOCKER sin comillas a proposito: las pruebas lo cambian por "bash docker_falso.sh".
reemplazar_contenedor() {
    $DOCKER rm -f calculadora > /dev/null 2>&1 || true
    $DOCKER run -d --name calculadora --restart unless-stopped \
        -p 80:8000 -v calculadora-datos:/app/instance \
        --env-file "$CALC_DIR/calculadora.env" "$1" > /dev/null
}

desplegar() {
    if [ $# -ne 1 ] || [ -z "$1" ]; then
        echo "Uso: desplegar.sh <tag>" >&2
        exit 2
    fi
    local tag="$1" secreto tenia_actual=no

    # El secreto llega por stdin: nunca se imprime ni va en la linea de comandos.
    secreto="$(cat)"
    if [ -z "$secreto" ]; then
        echo "Falta SECRET_KEY por stdin" >&2
        exit 2
    fi

    mkdir -p "$CALC_DIR"
    local env_file="$CALC_DIR/calculadora.env"
    ( umask 077; printf 'SECRET_KEY=%s\n' "$secreto" > "$env_file" )
    chmod 600 "$env_file"
    secreto=""

    if $DOCKER image inspect calculadora:actual > /dev/null 2>&1; then
        $DOCKER tag calculadora:actual calculadora:anterior
        tenia_actual=si
    fi

    $DOCKER tag "calculadora:$tag" calculadora:actual

    if reemplazar_contenedor "calculadora:$tag"; then
        echo "Desplegada calculadora:$tag"
        return 0
    fi

    echo "No arrancó calculadora:$tag" >&2
    if [ "$tenia_actual" = si ]; then
        $DOCKER tag calculadora:anterior calculadora:actual
        if reemplazar_contenedor calculadora:actual; then
            echo "Se restauró la versión anterior" >&2
        else
            echo "No se pudo restaurar la versión anterior" >&2
        fi
    else
        echo "No hay versión anterior para restaurar" >&2
    fi
    exit 1
}

# Solo corre el flujo principal si se ejecuta directamente (no con source).
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    desplegar "$@"
fi
