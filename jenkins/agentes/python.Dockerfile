# Java 21 (el controlador usa 21 y agent.jar no corre en 17); bookworm solo trae 17
FROM eclipse-temurin:21-jre AS java

FROM python:3.12-slim-bookworm

ARG DOCKER_VERSION=29.10.0
ARG SONAR_SCANNER_VERSION=8.5.0.16571

COPY --from=java /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:$PATH

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      openssh-client curl git unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Binario estático del cliente docker (usa el socket de la laptop)
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" \
  | tar -xz -C /usr/local/bin --strip-components=1 docker/docker

# sonar-scanner-cli
RUN curl -fsSL -o /tmp/sonar.zip "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux-x64.zip" \
 && unzip -q /tmp/sonar.zip -d /opt \
 && mv /opt/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64 /opt/sonar-scanner \
 && ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner \
 && rm /tmp/sonar.zip

# Corre como root para poder usar el socket de Docker Desktop (simplificación de demo)
COPY agentes/arrancar-agente.sh /usr/local/bin/arrancar-agente.sh
RUN chmod +x /usr/local/bin/arrancar-agente.sh
WORKDIR /home/jenkins
ENTRYPOINT ["/usr/local/bin/arrancar-agente.sh"]
