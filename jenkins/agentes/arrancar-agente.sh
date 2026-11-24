#!/bin/sh
# Descarga agent.jar del controlador y conecta este contenedor como agente (WebSocket).
set -eu

: "${JENKINS_URL:?falta JENKINS_URL}"
: "${SECRETO:?falta SECRETO (secreto del nodo en .env)}"
: "${NOMBRE:?falta NOMBRE (nombre del nodo)}"

mkdir -p /home/jenkins/agent
cd /home/jenkins

# El controlador puede tardar en arrancar: reintenta la descarga.
until curl -fsS -o agent.jar "$JENKINS_URL/jnlpJars/agent.jar"; do
  echo "Esperando al controlador en $JENKINS_URL ..."
  sleep 5
done

exec java -jar agent.jar -url "$JENKINS_URL" -secret "$SECRETO" -name "$NOMBRE" \
  -webSocket -workDir /home/jenkins/agent
