#!/usr/bin/env bash
# Docker falso para las pruebas: anota cada llamada en $DOCKER_LOG y
# simula las imagenes con el archivo $DOCKER_IMAGENES (una por linea).
# $DOCKER_IDS (opcional): lineas "imagen id" con el ID de cada imagen; si no
# esta, el ID de una imagen es su nombre. `tag` copia el ID del origen.
# $DOCKER_FALLAR_RUN (opcional): si el `run` incluye ese argumento, falla.
echo "$*" >> "$DOCKER_LOG"

id_de() {
    local id=""
    if [ -n "${DOCKER_IDS:-}" ] && [ -f "$DOCKER_IDS" ]; then
        id="$(awk -v n="$1" '$1==n {v=$2} END {print v}' "$DOCKER_IDS")"
    fi
    echo "${id:-$1}"
}

if [ "${1:-}" = "image" ] && [ "${2:-}" = "inspect" ]; then
    imagen="${!#}"
    grep -qxF -- "$imagen" "$DOCKER_IMAGENES" || exit 1
    case "$*" in *--format*) id_de "$imagen" ;; esac
    exit 0
fi

if [ "${1:-}" = "tag" ]; then
    echo "$3" >> "$DOCKER_IMAGENES"
    if [ -n "${DOCKER_IDS:-}" ]; then
        echo "$3 $(id_de "$2")" >> "$DOCKER_IDS"
    fi
fi

if [ "${1:-}" = "run" ] && [ -n "${DOCKER_FALLAR_RUN:-}" ]; then
    case " $* " in *" $DOCKER_FALLAR_RUN "*) echo "run falso fallo" >&2; exit 125 ;; esac
fi
exit 0
