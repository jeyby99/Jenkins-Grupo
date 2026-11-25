# Guion de la demo de Jenkins (12 minutos)

Exposición de 20 min: 8 de diapositivas y 12 de demo. Este guion es solo la demo.
Regla de oro: si algo se traba más de 20 segundos, pasa al plan B y sigue hablando.

Nunca muestres en pantalla: "Información del sistema" (de un nodo o del controlador), `jenkins/.env`, el `.pem` ni el valor de ninguna
credencial. En Jenkins se muestran las credenciales **solo por ID**. En los
registros se ve `****`.

## Antes (30 min antes de empezar)

Hazlo en el aula, con la red del aula.

- [ ] Enciende el Learner Lab y espera a que la EC2 esté en *running*. La sesión dura
      4 h: no la enciendas más temprano de lo necesario.
- [ ] En AWS, **Security Group** de la EC2 de la demo: edita la regla del puerto 22 y
      ponla en **Mi IP** *desde la red del aula*. En otra red tu IP cambia y el SSH
      queda bloqueado. El puerto 80 queda abierto. La IP elástica no cambia.
- [ ] Prueba el SSH desde tu laptop: `ssh -i <tu-llave>.pem ec2-user@<IP-ELASTICA> "docker ps"`
      (no dejes el `.pem` ni el comando a la vista).
- [ ] Levanta Jenkins:
      ```powershell
      cd jenkins
      docker compose up -d
      docker compose up -d smee
      ```
      El segundo comando enciende el relé del webhook (perfil `webhook`) y necesita
      `SMEE_URL` en `jenkins/.env`.
- [ ] Abre http://localhost:8080 (usuario `admin`). En **Administrar Jenkins → Nodos**:
      `agente-python` y `agente-browser` en línea.
- [ ] Revisa que existan las credenciales (solo mira los IDs): `sonarcloud-token`,
      `ec2-demo-ssh`, `ec2-demo-host`, `calculadora-secret-key`, `github-token`,
      `azure-sp-ejemplo`, `gcp-sa-ejemplo`.
- [ ] **Ensayo en orden** (hazlo todo en `jenkins-correcciones`; la rama `main` falla la
      calidad a propósito y nunca llega al despliegue). `origin/main` es la única base:
      el `main` local puede estar viejo.
      1. **Poner las 3 correcciones ensayando el plan B.** Esto también prueba el webhook:
         ```powershell
         git fetch origin
         git rebase origin/main respaldo-correcciones
         git push origin respaldo-correcciones:jenkins-correcciones --force-with-lease
         ```
         Revisa `docker compose logs smee` (sin errores) y que la ejecución nueva de
         `jenkins-correcciones` aparezca en menos de ~15 s. Si no llega, pollSCM
         (cada 2 min) es el respaldo. Comprueba que **un push produjo exactamente una
         ejecución**: `githubPush` y los eventos del origen de ramas pueden duplicarla.
         Si aparece una repetida, aborta la sobrante (quitar `githubPush()` del
         `Jenkinsfile` es el arreglo para después de la demo). Si es la primera vez, antes haz
         `git fetch origin` y `git switch jenkins-correcciones` para tenerla en local.
      2. **Ejecución verde con `DESTINO=aws`**: la que acabas de lanzar. Pulsa
         **Desplegar** en "Aprobación". Deja una versión en la EC2. Entra a
         `http://<IP-ELASTICA>` y registra el usuario de demo (por ejemplo `demo`, con una
         clave que no uses en otro sitio): el volumen de la EC2 lo conserva.
      3. **Ejecución guardada con `DESTINO=azure-ejemplo`**
         (**Construir con parámetros**) y clic en **Desplegar**.
      4. **Ejecución guardada con `SIMULAR_FALLA_SALUD=true`**, **después** del paso 2
         (el rollback necesita una versión anterior distinta en la EC2; si es el primer
         despliegue, termina con "no se pudo volver a la versión anterior"). Clic en
         **Desplegar**.
      5. En las ejecuciones de los pasos 2, 3 y 4 pulsa **Mantener esta ejecución para
         siempre**: Jenkins guarda solo las últimas 15 y las del cron, del pollSCM o las
         abortadas las sacarían. Anota sus números.
      6. **Solo entonces, restaura la rama** para que vuelva a fallar en la demo:
         ```powershell
         git fetch origin
         git switch jenkins-correcciones
         git reset --hard origin/main
         git push --force-with-lease origin jenkins-correcciones
         ```
         Revisa con `git log --oneline -3` que apunta al mismo commit que `origin/main`.
         Deja que la ejecución nueva termine (sale roja) o abórtala.
- [ ] **Aborta (no apruebes) cualquier ejecución que esté esperando en "Aprobación".** Las ejecuciones
      automáticas (webhook, pollSCM cada 2 min, cron de lunes a viernes ~7 h) arrancan con
      `DESTINO=aws` y se detienen ahí; terminan en ABORTED a los 10 min. Como no se
      permiten ejecuciones simultáneas, las nuevas hacen cola detrás de ellas.
- [ ] Deja otra vez lista la rama de respaldo para el plan B (el `git rebase` del paso 1
      la dejó sobre `origin/main`; si `origin/main` cambió, repítelo):
      ```powershell
      git fetch origin
      git rebase origin/main respaldo-correcciones
      ```
      Sin este rebase, el `push --force-with-lease` del plan B no sirve.
- [ ] Pestañas abiertas, en este orden:
      1. Jenkins (http://localhost:8080)
      2. GitHub: repo `jeyby99/Jenkins-Grupo` (con los 3 issues a mano)
      3. SonarCloud: el proyecto, con la vulnerabilidad de `app/config.py` (regla `python:S2068`)
      4. `http://<IP-ELASTICA>`
- [ ] VS Code abierto con `app/config.py`, `app/tarifas.py`, `app/rutas.py` y el
      `Jenkinsfile`. Terminal en la carpeta del repo.
- [ ] Internet: si el aula falla, hotspot del celular (y recuerda que la regla del
      puerto 22 depende de tu IP: si cambias de red, vuelve a poner "Mi IP").
- [ ] Video de respaldo abierto en el reproductor, en pausa.

## Minuto a minuto

| Min | Qué pasa | Qué dices | Comando o clic | Plan B |
|-----|----------|-----------|----------------|--------|
| 0–1.5 | Jenkins por dentro | "Esto es Jenkins. Un controlador que manda y dos agentes que trabajan: uno de Python y uno con navegador. Los secretos viven aquí; en el repo solo hay sus nombres." | Pestaña Jenkins → **Administrar Jenkins → Nodos** (2 en línea). Luego **Credenciales** (solo IDs, sin abrir ninguna). Luego el job `calculadora-pasajes` y sus ramas | Captura de pantalla de los nodos |
| 1.5–4 | Cambio en `main` → webhook → 3 rojos | "Subo un cambio pequeño. GitHub avisa por webhook y Jenkins arranca solo. La calidad corre en paralelo en los dos agentes." Mientras corre, recorre el `Jenkinsfile`: `parallel`, `agent`, `catchError`, `input`, `triggers`. | Terminal: `git switch main`, `git pull origin main`, `git commit --allow-empty -m "Dispara la demo"`, `git push origin main`. En Jenkins: rama `main` → vista de etapas | Esperar hasta 2 min (pollSCM) o **Construir ahora** en `main` |
| 4–6 | Leer los 3 rojos | "Tres revisiones, tres fallos a la vez. Cada una atrapó un error distinto." | Etapa **Unitarias** → resultados de pytest (falla la tarifa del 1 de enero). Etapa **SonarCloud** → vulnerabilidad `python:S2068` en `app/config.py`. El Quality Gate solo revisa código nuevo y se muestra como aviso informativo; la etapa se pone en rojo por la revisión de credenciales del pipeline (`ci/revisar_secretos.py`), que reporta `python:S2068` en `app/config.py:13`. **Navegador** → artefactos → captura con el error 500 | Abrir la ejecución anterior guardada en `main` |
| 6–8 | Corregir en `jenkins-correcciones` y empezar la ejecución | "Son tres líneas. Cada commit menciona su issue y GitHub los enlaza." Al empujar (~min 7) la calidad tarda 3-4 min: llénalos explicando cada arreglo, la vulnerabilidad de Sonar, los issues y el PR, y las etapas del `Jenkinsfile`. | Ver la sección siguiente. Al final `git push origin jenkins-correcciones`. En Jenkins: rama `jenkins-correcciones` | `git push origin respaldo-correcciones:jenkins-correcciones --force-with-lease` |
| 8–10.5 | Aprobación → AWS → salud OK → app | "Todo verde. Ahora decide una persona. Aprobamos y la imagen viaja por SSH hasta la EC2." | En la etapa **Aprobación** pulsa **Desplegar** (rápido: el timeout global de 20 min incluye la espera). Mientras esperas explica: la aprobación es una puerta humana; la imagen viaja por SSH con `docker save`, sin registro; en el registro el host y la clave salen como `****`; la verificación de salud hace hasta 5 intentos y, si falla, vuelve a la versión anterior. Mira **Desplegar** y **Verificar salud** (si la app responde, es inmediato; una verificación que falla tarda ~20-45 s, 5 intentos, antes del rollback). Abre `http://<IP-ELASTICA>`, entra con el usuario de demo y calcula un pasaje (2 viajes, 20 días, fecha 2027-01-01): con las correcciones da **$16.00** (40 pasajes × $0.40). **Regla de corte:** si al minuto 10 la ejecución aún no está verde, abre la ejecución verde guardada de `jenkins-correcciones` y sigue desde ahí | Video de respaldo |
| 10.5–12 | Multi-nube, rollback, cron y PR | "El destino es un parámetro: Azure es simulado, y lo decimos. Si la salud falla, Jenkins vuelve solo a la versión anterior." | Abre la ejecución guardada con `DESTINO=azure-ejemplo` (aviso `SIMULADO`). Luego la de `SIMULAR_FALLA_SALUD` y lee: "La verificación de salud falló: se volvió a la versión anterior". Enseña `cron` en el `Jenkinsfile`. En GitHub abre el PR `jenkins-correcciones` → `main`: marca verde y issues enlazados | Video o capturas de esas ejecuciones |

Notas de tiempo:

- La etapa de calidad dura 3-4 min. Por eso en el minuto 10.5–12 se muestran
  ejecuciones ya hechas: lanzar una nueva y esperarla no cabe.
- Si vas atrasado, deja el PR para el final y sáltate el cron.
- Los tiempos reales: push ~min 7, verde ~min 9.5-10, despliegue y salud ~min 10.5. Por eso
  la regla de corte del minuto 10 y el material guardado del último tramo.
- Al llegar al minuto 12, cierra aunque falte algo.

## Las 3 correcciones en vivo

Rama: `jenkins-correcciones` (`git switch jenkins-correcciones`).
Un commit por corrección y un solo `push` al final.

**Error 1: contraseña escrita en el código** (issue #1, lo detecta SonarCloud)

Archivo `app/config.py`, línea 13. Cambia:

```python
DB_PASSWORD = "Qu1t0-Pasaje-2026!"
```

por:

```python
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
```

```powershell
git add app/config.py
git commit -m "Corrige el error 1: la contraseña sale del entorno (#1)"
```

**Error 2: la tarifa nueva debe valer desde el 1 de enero** (issue #2, lo detecta pytest)

Archivo `app/tarifas.py`, línea 24. Cambia:

```python
    if fecha > FECHA_CAMBIO:
```

por:

```python
    if fecha >= FECHA_CAMBIO:
```

```powershell
git add app/tarifas.py
git commit -m "Corrige el error 2: la tarifa nueva aplica desde el 1 de enero (#2)"
```

**Error 3: viajes y días llegan como texto** (issue #3, lo detecta Playwright)

Archivo `app/rutas.py`, líneas 44 y 45. Cambia:

```python
            viajes = request.form["viajes"]
            dias = request.form["dias"]
```

por:

```python
            viajes = int(request.form["viajes"])
            dias = int(request.form["dias"])
```

```powershell
git add app/rutas.py
git commit -m "Corrige el error 3: viajes y días se convierten a número (#3)"
git push origin jenkins-correcciones
```

Los comentarios que hay encima de cada línea no hace falta tocarlos: la corrección
es solo la línea.

**El PR, sin fusionar.** Al final del minuto 10.5–12, en GitHub: **Compare & pull
request** de `jenkins-correcciones` hacia `main`. Muestra la marca verde de Jenkins y
los issues #1, #2 y #3 enlazados. **NO pulses Merge.** Los issues quedan enlazados;
si quieres, ciérralos a mano.

## Si algo falla

| Problema | Qué hacer |
|----------|-----------|
| El webhook no llega y la ejecución no arranca | Espera hasta 2 min: `pollSCM` revisa el repo solo. O abre la rama y pulsa **Construir ahora**. Mientras, sigue con el `Jenkinsfile`. |
| Hay una ejecución vieja esperando en "Aprobación" y la nueva está en cola | Ábrela y **aborta** (no apruebes). Decide rápido. |
| El push de las correcciones falla o se te traba el tecleo | `git push origin respaldo-correcciones:jenkins-correcciones --force-with-lease`. Solo funciona si antes hiciste `git fetch origin` y `git rebase origin/main respaldo-correcciones` (ver "Antes"). Di: "Tengo las mismas correcciones ya preparadas". |
| La calidad o el despliegue tardan demasiado | Abre la ejecución anterior guardada y cuenta desde ahí. |
| `Permission denied (publickey)` en `scp`/`ssh` | La credencial `ec2-demo-ssh` falta o es incorrecta, o la regla del puerto 22 no está en "Mi IP". Revisa ambas. |
| SSH a la EC2 se rechaza o se agota | Casi seguro es la regla del puerto 22: cambió tu IP. Pon "Mi IP" de nuevo en el Security Group. Si no hay tiempo, pasa al video. |
| Es el primer despliegue en esa EC2 y se pide el rollback | Termina con "La verificación de salud falló y no se pudo volver a la versión anterior (ver registro)". Por eso la ejecución de prueba y el despliegue verde van antes. |
| No hay internet o el lab se cayó | Hotspot del celular. Si no se resuelve, **video de respaldo** (`docs/demo/tomas-video.md` es su lista de tomas). |
| Pasó mucho tiempo en "Aprobación" | A los 10 min se aborta, y los 20 min globales incluyen esa espera. Aprueba pronto. |

## Después

- [ ] Aborta cualquier ejecución que siga esperando en "Aprobación".
- [ ] **Apaga el lab** (AWS Academy → *End Lab*).
- [ ] `docker compose --profile webhook down` en `jenkins/` (sin `-v`, para conservar el historial).
- [ ] **Al terminar el semestre: libera la IP elástica.** Con la instancia apagada cobra
      cerca de USD 3.6 al mes.
- [ ] No fusiones el PR de `jenkins-correcciones`.
