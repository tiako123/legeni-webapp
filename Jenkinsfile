// Pipeline CI/CD Legeni WebApp
// qualité (en parallèle) -> build -> scan Trivy -> push -> staging -> validation humaine -> production
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    environment {
        IMAGE               = 'tiako123/legeni-webapp'
        VERSION             = sh(script: 'cat VERSION', returnStdout: true).trim()
        TAG                 = "${VERSION}-${BUILD_NUMBER}"
        K8S_AUTH_KUBECONFIG = credentials('kubeconfig')
        VAULT_FILE          = credentials('ansible-vault-pass')
    }

    stages {
        stage('Contrôles qualité') {
            parallel {
                stage('Tests + couverture') {
                    steps {
                        sh '''
                            docker build --target test -t legeni-webapp:test-$BUILD_NUMBER .
                            rm -rf reports && mkdir reports
                            cid=$(docker create legeni-webapp:test-$BUILD_NUMBER)
                            docker cp $cid:/reports/. reports/
                            docker rm $cid
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                            script {
                                try {
                                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                                } catch (Throwable t) {
                                    echo "Rapport de couverture non publié : ${t.message}"
                                }
                            }
                        }
                    }
                }
                stage('Flake8') {
                    steps {
                        sh 'docker build --target lint -t legeni-webapp:lint-$BUILD_NUMBER .'
                    }
                }
                stage('Hadolint') {
                    steps {
                        sh 'docker run --rm -i hadolint/hadolint:v2.12.0 < Dockerfile'
                    }
                }
                stage('Syntaxe Ansible') {
                    steps {
                        dir('ansible') {
                            sh 'ansible-playbook deploy.yml --syntax-check'
                        }
                    }
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --build-arg APP_VERSION=$VERSION -t $IMAGE:$TAG .'
            }
        }

        stage('Scan Trivy') {
            steps {
                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache/ aquasec/trivy:latest image --severity CRITICAL --ignore-unfixed --exit-code 1 --no-progress $IMAGE:$TAG'
            }
        }

        stage('Push Docker Hub') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'registry-credentials', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        export DOCKER_CONFIG="$WORKSPACE/.docker"
                        mkdir -p "$DOCKER_CONFIG"
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        docker push "$IMAGE:$TAG"
                        docker logout
                        rm -rf "$DOCKER_CONFIG"
                    '''
                }
            }
        }

        stage('Déploiement staging') {
            when { branch 'main' }
            steps {
                dir('ansible') {
                    sh 'ansible-playbook deploy.yml -e target_env=staging -e build_number=$BUILD_NUMBER --vault-password-file $VAULT_FILE'
                }
            }
        }

        stage('Validation humaine') {
            when { branch 'main' }
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input message: "Staging OK en ${env.TAG}. Déployer en production ?", ok: 'Déployer en production'
                }
            }
        }

        stage('Déploiement production') {
            when { branch 'main' }
            steps {
                dir('ansible') {
                    sh 'ansible-playbook deploy.yml -e target_env=prod -e build_number=$BUILD_NUMBER --vault-password-file $VAULT_FILE'
                }
            }
        }
    }

    post {
        always {
            sh 'docker rmi legeni-webapp:test-$BUILD_NUMBER legeni-webapp:lint-$BUILD_NUMBER || true'
            sh 'rm -rf .docker'
        }
        success {
            echo "Image ${IMAGE}:${TAG} construite et validée"
        }
        failure {
            script {
                try {
                    withCredentials([string(credentialsId: 'notify-webhook', variable: 'HOOK')]) {
                        sh 'curl -s -H "Content-Type: application/json" -d "{\\"content\\": \\"❌ $JOB_NAME #$BUILD_NUMBER en échec\\"}" "$HOOK"'
                    }
                } catch (Throwable t) {
                    echo 'Notification non envoyée : identifiant notify-webhook absent'
                }
            }
        }
    }
}
