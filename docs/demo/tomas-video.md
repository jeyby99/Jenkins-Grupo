# Lista de tomas del video de respaldo

Un ensayo completo con el lab encendido. Mismo orden que `guion.md`. Si una toma sale
mal, repítela sola: no hace falta grabar todo de nuevo.

Antes de grabar: lo mismo que "Antes" en `guion.md` (EC2 en *running*, regla del
puerto 22 en "Mi IP", Jenkins arriba, nada esperando en "Aprobación", ejecución de
prueba hecha). Graba la pantalla completa y tu voz. No muestres `jenkins/.env`, el
`.pem`, "Información del sistema" ni valores de credenciales.

| # | Toma | Qué se ve | Duración |
|---|------|-----------|----------|
| 1 | Jenkins por dentro | Nodos: `agente-python` y `agente-browser` en línea. Credenciales (solo IDs). Job `calculadora-pasajes` con sus ramas | 1.5 min |
| 2 | Cambio en `main` | `git commit --allow-empty -m "Dispara la demo"` y `git push origin main` | 0.5 min |
| 3 | Webhook y calidad en paralelo | Jenkins arranca solo; vista de etapas con las dos ramas corriendo a la vez | 1 min |
| 4 | Recorrido del Jenkinsfile | `parallel`, `agent`, `catchError`, `input`, `triggers`, mientras corre la ejecución | 1.5 min |
| 5 | Los 3 rojos | Tres etapas en rojo (Unitarias, SonarCloud, Navegador). Reporte de pytest (tarifa). SonarCloud: vulnerabilidad `python:S2068` en `app/config.py`. Captura de Playwright con el error 500 | 2 min |
| 6 | Corrección del error 1 | `app/config.py` línea 13 y commit con `(#1)` | 0.7 min |
| 7 | Corrección del error 2 | `app/tarifas.py` línea 24 y commit con `(#2)` | 0.7 min |
| 8 | Corrección del error 3 | `app/rutas.py` líneas 44-45, commit con `(#3)` y `git push origin jenkins-correcciones` | 0.8 min |
| 9 | Ejecución en verde | Rama `jenkins-correcciones`: calidad en verde y construcción de la imagen | 1.5 min |
| 10 | Aprobación | Etapa **Aprobación** y clic en **Desplegar** | 0.5 min |
| 11 | Despliegue en AWS | **Desplegar** (imagen por SSH, `****` en el registro) y **Verificar salud** en verde | 1 min |
| 12 | La app en la nube | `http://<IP-EC2>:8090`: entrar y calcular un pasaje (2 viajes, 20 días, 2027-01-01): resultado **$16.00** (40 pasajes × $0.40) | 0.8 min |
| 13 | Multi-nube | Ejecución con `DESTINO=azure-ejemplo`: aviso `SIMULADO: no se ejecuta` | 0.7 min |
| 14 | Rollback | Ejecución con `SIMULAR_FALLA_SALUD=true`: "La verificación de salud falló: se volvió a la versión anterior" | 1 min |
| 15 | Cron y PR | `cron` en el `Jenkinsfile`; PR `jenkins-correcciones` → `main` con la marca verde y los issues #1, #2 y #3. Sin fusionar | 0.8 min |

Total de tomas: 15 min en bruto. Al editar, acelera las esperas (tomas 3, 9 y 11) y
queda en 12 min o menos.

Consejos:

- La toma 14 necesita una versión anterior en la EC2: grábala después de la toma 11.
- Guarda el video en tu laptop y en una memoria USB, y pruébalo con el proyector.
