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
inicio el job multirrama `calculadora-pasajes` (origen `Jeyby99/Jenkins-Grupo4`).
El escaneo del repo fallará hasta que exista en GitHub y exista la credencial `github-token`.

`jenkins/.env` está en `.gitignore`: nunca se sube al repo.

## Credenciales (se crean a mano)

En **Administrar Jenkins → Credenciales → Global → Add Credentials**. El repo solo
guarda los IDs; los valores no están en ningún archivo.

| ID | Tipo | Para qué |
|----|------|----------|
| `sonarcloud-token` | Texto secreto | sonar-scanner |
| `ec2-demo-ssh` | Usuario + llave privada SSH | `ec2-user` de la EC2 de la demo |
| `ec2-demo-host` | Texto secreto | IP elástica de la EC2 |
| `calculadora-secret-key` | Texto secreto | `SECRET_KEY` de Flask en producción |
| `github-token` | Usuario + token | estado del commit en GitHub (marca verde/roja) |
| `azure-sp-ejemplo`, `gcp-sa-ejemplo` | Texto secreto con valor de relleno | solo para mostrar cómo se haría; nunca son reales |

Jenkins oculta los secretos en los registros (`****`).

## Secreto de cada agente

Los agentes se conectan al controlador con un secreto que genera Jenkins:

1. Entra a **Administrar Jenkins → Nodos → `agente-python`**.
2. Verás una línea de comando con `-secret <valor largo>`. Copia solo ese valor.
3. Pégalo en `jenkins/.env` como `SECRETO_AGENTE_PYTHON=<valor>`.
4. Repite con `agente-browser` y `SECRETO_AGENTE_BROWSER`.

## Pendiente (próximos pasos)

- Los contenedores de los agentes se agregan al `docker-compose.yml` más adelante.
- `SMEE_URL` es para el relé de webhooks de GitHub, que también se agrega después.
