#!/usr/bin/env bash
# Docker falso para las pruebas: anota cada llamada en $DOCKER_LOG y
# simula las imagenes con el archivo $DOCKER_IMAGENES (una por linea).
echo "$*" >> "$DOCKER_LOG"

if [ "${1:-}" = "image" ] && [ "${2:-}" = "inspect" ]; then
    grep -qxF -- "$3" "$DOCKER_IMAGENES"
    exit $?
fi

if [ "${1:-}" = "tag" ]; then
    echo "$3" >> "$DOCKER_IMAGENES"
fi
exit 0
