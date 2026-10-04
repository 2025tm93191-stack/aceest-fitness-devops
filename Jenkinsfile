pipeline {
    agent any

    // Poll GitHub every 5 minutes. Replace with githubPush() once a webhook is configured.
    triggers {
        pollSCM('H/5 * * * *')
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        IMAGE = "aceest-fitness"
        TAG   = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Clean Environment') {
            steps {
                sh '''
                    rm -rf .venv
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m compileall -q app.py fitness tests
                    flake8 .
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest --junitxml=reports/junit.xml --cov=fitness --cov=app --cov-report=xml:reports/coverage.xml
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build --target runtime -t ${IMAGE}:${TAG} -t ${IMAGE}:latest .'
            }
        }

        stage('Container Tests') {
            steps {
                sh '''
                    docker build --target test -t ${IMAGE}:test .
                    docker run --rm ${IMAGE}:test
                '''
            }
        }
    }

    post {
        success { echo "Build ${env.BUILD_NUMBER} passed the quality gate." }
        failure { echo "Build ${env.BUILD_NUMBER} failed. Check the stage logs above." }
        always  { sh 'docker image prune -f || true' }
    }
}
