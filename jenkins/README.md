# Jenkins de la demo

Jenkins corre en tu laptop con Docker Compose y se configura solo, desde código:
el controlador usa JCasC (`controlador/casc.yaml`) y Job DSL para crear los nodos,
el servidor SonarCloud y el job `calculadora-pasajes`. El controlador tiene
0 ejecutores: todo el trabajo lo hacen los agentes.

## Cómo levantarlo

```powershell
cd jenkins
copy .env.ejemplo .env      # luego edita .env y pon tu contraseña en JENKINS_ADMIN_PASSWORD
docker compose up -d --build controlador
```

Abre http://localhost:8080 e inicia sesión con el usuario `admin` y la contraseña de
`JENKINS_ADMIN_PASSWORD`. En **Administrar Jenkins → Nodos** verás `agente-python`
(etiqueta `python`) y `agente-browser` (etiqueta `browser`) desconectados, y en el
inicio el job multirrama `calculadora-pasajes` (origen `jeyby99/Jenkins-Grupo`).
El escaneo del repo fallará hasta que exista en GitHub y exista la credencial `github-token`.

`jenkins/.env` está en `.gitignore`: nunca se sube al repo. Cada servicio recibe solo
las variables que necesita (`environment:` en el compose), y Jenkins solo escucha en
`127.0.0.1:8080`: no se puede abrir desde otros equipos de la red.
## Credenciales (se crean a mano)

En **Administrar Jenkins → Credenciales → Global → Add Credentials**. El repo solo
guarda los IDs; los valores no están en ningún archivo.

| ID | Tipo | Para qué |
|----|------|----------|
| `sonarcloud-token` | Texto secreto | sonar-scanner |
| `ec2-demo-ssh` | Usuario + llave privada SSH | `ec2-user` de la EC2 (compartida con PrograWeb) |
| `ec2-demo-host` | Texto secreto | IP pública de la EC2 (la app queda en el puerto 8090) |
| `calculadora-secret-key` | Texto secreto | `SECRET_KEY` de Flask en producción |
| `github-token` | Usuario + token | estado del commit en GitHub (marca verde/roja). Token clásico: `repo:status` + `public_repo` (repo público). Token fine-grained: Commit statuses: Read and write, Contents: Read-only, Metadata: Read-only |
| `azure-sp-ejemplo`, `gcp-sa-ejemplo` | Texto secreto con valor de relleno | solo para mostrar cómo se haría; nunca son reales |

Jenkins oculta los secretos en los registros (`****`).

## Secreto de cada agente

Los agentes se conectan al controlador con un secreto que genera Jenkins. Lo más simple
es sacarlo de la consola de scripts (**Administrar Jenkins → Consola de scripts**):

```groovy
println jenkins.model.Jenkins.get().getComputer('agente-python').getJnlpMac()
println jenkins.model.Jenkins.get().getComputer('agente-browser').getJnlpMac()
```

Pega cada valor en `jenkins/.env` como `SECRETO_AGENTE_PYTHON=<valor>` y
`SECRETO_AGENTE_BROWSER=<valor>`. (También aparece en **Nodos → el agente**, en la línea
con `-secret`.) Luego levanta todo:

```powershell
docker compose up -d --build
```

## Los agentes

- `agente-python` (etiqueta `python`): Python 3.12, sonar-scanner, cliente `docker`
  (usa el socket de Docker Desktop), `ssh`, `scp` y `curl`.
- `agente-browser` (etiqueta `browser`): Python 3.12 y Chromium de Playwright
  (imagen oficial de Playwright; la versión de `playwright` en `requirements.txt` debe
  coincidir con la de la imagen en `agentes/browser.Dockerfile`).
- Ambos comparten el volumen `pip-cache` para no descargar paquetes en cada ejecución.
- Simplificación de demo: `agente-python` corre como root y monta
  `/var/run/docker.sock` para poder construir imágenes. No es una práctica de producción.

## Webhook de GitHub (smee)

GitHub no puede llegar a tu laptop, así que el servicio `smee` (smee-client 5.0.0)
recibe los avisos desde smee.io y los reenvía a `http://controlador:8080/github-webhook/`.

1. Entra a https://smee.io y pulsa **Start a new channel**. Copia el URL del canal.
2. Pégalo en `jenkins/.env` como `SMEE_URL=<url del canal>`. Debe estar puesto antes
   del paso 4; si falta, el contenedor se detiene con "Falta SMEE_URL en jenkins/.env".
3. En GitHub: **Settings → Webhooks → Add webhook**.
   - *Payload URL*: el mismo URL de smee.
   - *Content type*: `application/json`.
   - Eventos: **Just the push event** (solo `push`).
4. Levanta el relé (usa un perfil, por eso hay que nombrarlo):

   ```powershell
   docker compose up -d smee
   ```

   Si después editas `.env`, vuelve a ejecutar `docker compose up -d smee` para que el
   contenedor tome el valor nuevo.

5. Haz un commit pequeño en la rama `jenkins` y súbelo. Para confirmar, mira los registros:

   ```powershell
   docker compose logs controlador | Select-String "Received PushEvent"
   ```

   La ejecución de `calculadora-pasajes` debe empezar en menos de 15 segundos.
   Segunda confirmación: en GitHub, **Settings → Webhooks → Recent Deliveries** debe
   mostrar la entrega con respuesta 200. Si falla, revisa `docker compose logs smee`.
