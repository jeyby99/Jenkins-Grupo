FROM mcr.microsoft.com/playwright/python:v1.65.2-noble

RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-21-jre-headless git curl \
 && rm -rf /var/lib/apt/lists/*

# La imagen trae solo los navegadores: el paquete debe tener la misma versión que la imagen
RUN pip install --no-cache-dir --break-system-packages playwright==1.65.2

COPY agentes/arrancar-agente.sh /usr/local/bin/arrancar-agente.sh
RUN chmod +x /usr/local/bin/arrancar-agente.sh
WORKDIR /home/jenkins
ENTRYPOINT ["/usr/local/bin/arrancar-agente.sh"]
