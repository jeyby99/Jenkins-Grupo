#!/usr/bin/env bash
# Uso: bash rollback.sh
# Vuelve a calculadora:anterior y recrea el contenedor. Usa
# reemplazar_contenedor de desplegar.sh (misma carpeta).
set -euo pipefail

# shellcheck source=desplegar.sh
source "$(dirname "${BASH_SOURCE[0]}")/desplegar.sh"

if ! $DOCKER image inspect calculadora:anterior > /dev/null 2>&1; then
    echo "No hay versión anterior para volver"
    exit 1
fi

if [ ! -f "$CALC_DIR/calculadora.env" ]; then
    echo "Falta $CALC_DIR/calculadora.env: no se puede recrear el contenedor"
    exit 1
fi

# Si actual y anterior son la misma imagen, volver no cambiaria nada.
id_anterior="$($DOCKER image inspect --format '{{.Id}}' calculadora:anterior)"
id_actual="$($DOCKER image inspect --format '{{.Id}}' calculadora:actual 2> /dev/null || true)"
if [ "$id_anterior" = "$id_actual" ]; then
    echo "Ya se está usando la versión anterior"
    exit 1
fi

$DOCKER tag calculadora:anterior calculadora:actual
reemplazar_contenedor calculadora:actual

echo "Vuelta a la versión anterior"
