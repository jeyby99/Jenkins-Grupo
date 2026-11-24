// Pipeline de Jenkins: calidad, construcción, aprobación y despliegue.
// Cada vez que alguien sube código, Jenkins corre las revisiones en paralelo,
// en dos agentes distintos:
//   - agente 'python':  pruebas unitarias + SonarCloud
//   - agente 'browser': pruebas de navegador (Playwright)
// Si una revisión falla, las otras igual terminan: así vemos todos los errores
// de una sola vez.
// Si todo queda en verde: se construye la imagen, se pide aprobación, se
// despliega (aws de verdad; azure y gcp son simulados) y se verifica la salud,
// con vuelta a la versión anterior si falla.

pipeline {
    // Sin agente global: cada rama paralela pide el suyo.
    agent none

    options {
        timestamps()                                      // hora en cada línea del registro
        timeout(time: 20, unit: 'MINUTES')                // nada se queda colgado para siempre
        disableConcurrentBuilds()                         // una ejecución a la vez
        buildDiscarder(logRotator(numToKeepStr: '15'))    // guarda solo las últimas 15
    }

    parameters {
        choice(name: 'DESTINO', choices: ['aws', 'azure-ejemplo', 'gcp-ejemplo'],
               description: 'Nube a la que se despliega (solo aws está conectada)')
        booleanParam(name: 'SIMULAR_FALLA_SALUD', defaultValue: false,
                     description: 'Marcar para que la verificación de salud falle a propósito')
    }

    // Cuándo corre solo: al recibir un push, al revisar el repo cada 2 minutos
    // y todos los días hábiles por la mañana.
    triggers {
        githubPush()
        pollSCM('H/2 * * * *')
        cron('H 7 * * 1-5')
    }

    environment {
        // La etiqueta de la imagen (IMAGEN_TAG) se define en 'Construir imagen':
        // GIT_COMMIT solo existe después del checkout en un agente.
        APP = 'calculadora'
        // Opciones de SSH en un solo lugar: no preguntar por la huella y no esperar más de 10 s.
        SSH_OPTS = '-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10'
    }

    stages {
        stage('Calidad') {
            // Las dos ramas corren al mismo tiempo, cada una en su agente.
            parallel {
                stage('Unitarias y Sonar') {
                    agent { label 'python' }
                    steps {
                        sh '''
                            python3.12 -m venv .venv
                            . .venv/bin/activate
                            pip install -r requirements.txt
                        '''
                        // catchError marca la etapa en rojo pero deja seguir:
                        // así SonarCloud corre aunque pytest falle.
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            sh '''
                                . .venv/bin/activate
                                pytest tests/unitarias tests/despliegue --cov=app --cov-report=xml --junitxml=reporte-unitarias.xml
                            '''
                        }
                        // Análisis de SonarCloud; espera el veredicto del Quality Gate.
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            withSonarQubeEnv('SonarCloud') {
                                sh 'sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=180'
                            }
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reporte-unitarias.xml'
                            cleanWs()   // deja limpio el espacio de trabajo del agente
                        }
                    }
                }

                stage('Navegador') {
                    agent { label 'browser' }
                    steps {
                        sh '''
                            python3.12 -m venv .venv
                            . .venv/bin/activate
                            pip install -r requirements.txt
                        '''
                        // conftest.py levanta la app con una base temporal:
                        // no hace falta arrancar el servidor a mano.
                        // Si falla, guarda captura de pantalla y traza para verlas.
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            sh '''
                                . .venv/bin/activate
                                pytest tests/e2e --junitxml=reporte-e2e.xml --screenshot only-on-failure --tracing retain-on-failure
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reporte-e2e.xml'
                            archiveArtifacts artifacts: 'test-results/**', allowEmptyArchive: true
                            cleanWs()
                        }
                    }
                }
            }
        }

        // Solo se construye y se despliega si toda la calidad quedó en verde.
        stage('Construir imagen') {
            agent { label 'python' }
            when {
                beforeAgent true
                expression { currentBuild.currentResult == 'SUCCESS' }
            }
            steps {
                // GIT_COMMIT ya existe: el checkout se hizo al entrar al agente.
                script { env.IMAGEN_TAG = "${env.GIT_COMMIT.take(7)}-${env.BUILD_NUMBER}" }
                // La imagen queda en el Docker de la laptop; 'Desplegar' la reutiliza.
                // La etiqueta hace único el ID de cada imagen: así el rollback siempre tiene algo distinto a qué volver.
                sh 'docker build --label org.opencontainers.image.revision=${IMAGEN_TAG} -t calculadora:${IMAGEN_TAG} .'
            }
        }

        // Sin agente: esperar la aprobación no ocupa ningún ejecutor.
        stage('Aprobación') {
            agent none
            when { expression { currentBuild.currentResult == 'SUCCESS' } }
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    input message: "¿Desplegar ${params.DESTINO}?", ok: 'Desplegar'
                }
            }
        }

        stage('Desplegar') {
            agent { label 'python' }
            when {
                beforeAgent true
                expression { currentBuild.currentResult == 'SUCCESS' }
            }
            steps {
                script {
                    switch (params.DESTINO) {
                        case 'aws':
                            // El host y la clave vienen de credenciales: el registro muestra ****.
                            // Comillas simples: el secreto lo expande el shell, no Groovy.
                            withCredentials([string(credentialsId: 'ec2-demo-host', variable: 'HOST'),
                                             string(credentialsId: 'calculadora-secret-key', variable: 'SECRET_KEY')]) {
                                sshagent(['ec2-demo-ssh']) {
                                    // Copia los scripts (rollback.sh usa funciones de desplegar.sh).
                                    sh 'scp $SSH_OPTS aws/desplegar.sh aws/rollback.sh ec2-user@$HOST:calculadora/'
                                    // Envía la imagen comprimida por SSH, sin registro de imágenes.
                                    // Con bash y pipefail: si falla cualquier parte de la tubería, falla el paso.
                                    sh '''#!/bin/bash
set -eo pipefail
docker save calculadora:$IMAGEN_TAG | gzip | ssh $SSH_OPTS ec2-user@$HOST "gunzip | docker load"
'''
                                    // La clave viaja por la entrada estándar, nunca como argumento.
                                    sh '''#!/bin/bash
set -eo pipefail
printf "%s" "$SECRET_KEY" | ssh $SSH_OPTS ec2-user@$HOST "bash calculadora/desplegar.sh $IMAGEN_TAG"
'''
                                }
                            }
                            break
                        case 'azure-ejemplo':
                            echo '===== SIMULADO: no se ejecuta ====='
                            echo 'Así se desplegaría en Azure (credencial: azure-sp-ejemplo):'
                            echo 'az login --service-principal --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID   # azure-sp-ejemplo'
                            echo 'az webapp config container set --name calculadora --resource-group demo --docker-custom-image-name calculadora:' + env.IMAGEN_TAG
                            break
                        case 'gcp-ejemplo':
                            echo '===== SIMULADO: no se ejecuta ====='
                            echo 'Así se desplegaría en Google Cloud (credencial: gcp-sa-ejemplo):'
                            echo 'gcloud auth activate-service-account --key-file=$GCP_SA_KEY   # gcp-sa-ejemplo'
                            echo 'gcloud run deploy calculadora --image=calculadora:' + env.IMAGEN_TAG + ' --region=us-central1'
                            break
                        default:
                            error("Destino desconocido: ${params.DESTINO}")
                    }
                }
            }
        }

        stage('Verificar salud') {
            agent { label 'python' }
            when {
                beforeAgent true
                expression { currentBuild.currentResult == 'SUCCESS' && params.DESTINO == 'aws' }
            }
            environment {
                // /no-existe devuelve 404: sirve para ver el rollback en vivo.
                RUTA = "${params.SIMULAR_FALLA_SALUD ? '/no-existe' : '/login'}"
            }
            steps {
                withCredentials([string(credentialsId: 'ec2-demo-host', variable: 'HOST')]) {
                    script {
                        // 5 intentos, 5 segundos entre uno y otro.
                        def estado = sh(returnStatus: true, script: '''
                            for i in 1 2 3 4 5; do
                                if curl -fsS -o /dev/null --max-time 5 "http://$HOST$RUTA"; then
                                    echo "Intento $i: la app responde"
                                    exit 0
                                fi
                                echo "Intento $i de 5: sin respuesta"
                                [ "$i" -lt 5 ] && sleep 5
                            done
                            exit 1
                        ''')
                        if (estado != 0) {
                            // Falló la salud: se vuelve a la versión anterior.
                            sshagent(['ec2-demo-ssh']) {
                                // returnStatus: si el rollback falla, igual mostramos el mensaje correcto.
                                def r = sh(returnStatus: true, script: 'ssh $SSH_OPTS ec2-user@$HOST "bash calculadora/rollback.sh"')
                                error(r == 0 ? 'La verificación de salud falló: se volvió a la versión anterior'
                                             : 'La verificación de salud falló y no se pudo volver a la versión anterior (ver registro)')
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        success { echo 'Todo en verde: el código puede integrarse.' }
        failure { echo 'Algo falló: revisa la etapa en rojo.' }
    }
}
