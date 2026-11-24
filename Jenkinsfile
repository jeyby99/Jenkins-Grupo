// Pipeline de Jenkins: la parte de calidad.
// Cada vez que alguien sube código, Jenkins corre las revisiones en paralelo,
// en dos agentes distintos:
//   - agente 'python':  pruebas unitarias + SonarCloud
//   - agente 'browser': pruebas de navegador (Playwright)
// Si una revisión falla, las otras igual terminan: así vemos todos los errores
// de una sola vez.

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
        IMAGEN_TAG = "${GIT_COMMIT.take(7)}-${BUILD_NUMBER}"
        APP        = 'calculadora'
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
    }

    post {
        success { echo 'Todo en verde: el código puede integrarse.' }
        failure { echo 'Algo falló: revisa la etapa en rojo.' }
    }
}
