# CI/CD Integration

This guide shows how to integrate the Prometheus Testing Framework into CI/CD pipelines.

## Overview

The testing framework is designed for CI/CD integration with:

- Exit codes indicating pass (0) or fail (non-zero)
- JSON/Markdown/HTML report generation
- Configurable timeouts
- Parallel test execution support
- Resource cleanup after tests

## GitHub Actions

### Basic Sanity Tests

```yaml
# .github/workflows/prometheus-tests.yml
name: Prometheus Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  sanity-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r prometheus/requirements.txt

      - name: Start Prometheus
        run: |
          cd prometheus/install/docker
          docker-compose up -d
          sleep 10  # Wait for startup

      - name: Run sanity tests
        run: |
          cd prometheus
          python3 -m tests.cli run --type sanity --platform docker

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: prometheus/results/

      - name: Cleanup
        if: always()
        run: |
          cd prometheus/install/docker
          docker-compose down -v
```


### Full Test Suite with Minikube

```yaml
# .github/workflows/prometheus-full-tests.yml
name: Prometheus Full Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  full-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
            | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update && sudo apt-get install k6

      - name: Start Minikube
        uses: medyagh/setup-minikube@latest
        with:
          memory: 4096
          cpus: 2

      - name: Install Prometheus
        run: |
          helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
          helm install prometheus prometheus-community/kube-prometheus-stack \
            -n monitoring --create-namespace --wait --timeout 5m

      - name: Port forward Prometheus
        run: |
          kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
          sleep 5

      - name: Install test dependencies
        run: pip install -r prometheus/requirements.txt

      - name: Run tests
        run: |
          cd prometheus
          python3 -m tests.cli run \
            --platform minikube \
            --type sanity \
            --type integration \
            --type load \
            --k6-vus 20 \
            --k6-duration 5m \
            --output ./results

      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: prometheus/results/

      - name: Cleanup
        if: always()
        run: |
          cd prometheus
          python3 -m tests.cli cleanup --platform minikube --force
```

---

## GitLab CI

### Basic Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - report

variables:
  PYTHON_VERSION: "3.10"

sanity-tests:
  stage: test
  image: python:${PYTHON_VERSION}
  services:
    - docker:dind
  before_script:
    - pip install -r prometheus/requirements.txt
    - cd prometheus/install/docker && docker-compose up -d && sleep 10
  script:
    - cd prometheus
    - python3 -m tests.cli run --type sanity --platform docker
  after_script:
    - cd prometheus/install/docker && docker-compose down -v
  artifacts:
    paths:
      - prometheus/results/
    when: always
    expire_in: 1 week

load-tests:
  stage: test
  image: python:${PYTHON_VERSION}
  services:
    - docker:dind
  before_script:
    - apt-get update && apt-get install -y gnupg
    - curl -s https://dl.k6.io/key.gpg | apt-key add -
    - echo "deb https://dl.k6.io/deb stable main" | tee /etc/apt/sources.list.d/k6.list
    - apt-get update && apt-get install -y k6
    - pip install -r prometheus/requirements.txt
    - cd prometheus/install/docker && docker-compose up -d && sleep 10
  script:
    - cd prometheus
    - python3 -m tests.cli run --type load --platform docker --k6-vus 10 --k6-duration 5m
  after_script:
    - cd prometheus/install/docker && docker-compose down -v
  artifacts:
    paths:
      - prometheus/results/
    when: always
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"

generate-report:
  stage: report
  image: python:${PYTHON_VERSION}
  needs:
    - sanity-tests
  script:
    - pip install -r prometheus/requirements.txt
    - cd prometheus
    - python3 -m tests.cli report --input results/test_report.json --format html --format markdown
  artifacts:
    paths:
      - prometheus/results/
    when: always
```


---

## Jenkins

### Declarative Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.10'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r prometheus/requirements.txt'
            }
        }

        stage('Start Prometheus') {
            steps {
                dir('prometheus/install/docker') {
                    sh 'docker-compose up -d'
                    sh 'sleep 10'
                }
            }
        }

        stage('Sanity Tests') {
            steps {
                dir('prometheus') {
                    sh 'python3 -m tests.cli run --type sanity --platform docker'
                }
            }
        }

        stage('Load Tests') {
            when {
                branch 'main'
            }
            steps {
                dir('prometheus') {
                    sh '''
                        python3 -m tests.cli run \
                            --type load \
                            --platform docker \
                            --k6-vus 20 \
                            --k6-duration 10m
                    '''
                }
            }
        }
    }

    post {
        always {
            dir('prometheus/install/docker') {
                sh 'docker-compose down -v'
            }
            archiveArtifacts artifacts: 'prometheus/results/**/*', allowEmptyArchive: true
            publishHTML(target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'prometheus/results',
                reportFiles: 'test_report.html',
                reportName: 'Prometheus Test Report'
            ])
        }
        failure {
            emailext(
                subject: "Prometheus Tests Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Check console output at ${env.BUILD_URL}",
                recipientProviders: [developers()]
            )
        }
    }
}
```

---

## AWS CodePipeline

### buildspec.yml

```yaml
# buildspec.yml
version: 0.2

env:
  variables:
    PYTHON_VERSION: "3.10"

phases:
  install:
    runtime-versions:
      python: 3.10
    commands:
      - pip install -r prometheus/requirements.txt
      - curl -s https://dl.k6.io/key.gpg | apt-key add -
      - echo "deb https://dl.k6.io/deb stable main" | tee /etc/apt/sources.list.d/k6.list
      - apt-get update && apt-get install -y k6

  pre_build:
    commands:
      - cd prometheus/install/docker
      - docker-compose up -d
      - sleep 15

  build:
    commands:
      - cd prometheus
      - python3 -m tests.cli run --type sanity --type integration --platform docker

  post_build:
    commands:
      - cd prometheus/install/docker
      - docker-compose down -v

artifacts:
  files:
    - prometheus/results/**/*
  name: test-results

reports:
  prometheus-tests:
    files:
      - prometheus/results/test_report.json
    file-format: GENERICJSON
```

---

## Azure DevOps

### azure-pipelines.yml

```yaml
# azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.10'

stages:
  - stage: Test
    jobs:
      - job: SanityTests
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: pip install -r prometheus/requirements.txt
            displayName: 'Install dependencies'

          - script: |
              cd prometheus/install/docker
              docker-compose up -d
              sleep 10
            displayName: 'Start Prometheus'

          - script: |
              cd prometheus
              python3 -m tests.cli run --type sanity --platform docker
            displayName: 'Run sanity tests'

          - script: |
              cd prometheus/install/docker
              docker-compose down -v
            displayName: 'Cleanup'
            condition: always()

          - task: PublishTestResults@2
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: 'prometheus/results/*.xml'
            condition: always()

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: 'prometheus/results'
              artifactName: 'test-results'
            condition: always()

      - job: LoadTests
        dependsOn: SanityTests
        condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: |
              sudo gpg -k
              sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
                --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
              echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
                | sudo tee /etc/apt/sources.list.d/k6.list
              sudo apt-get update && sudo apt-get install k6
            displayName: 'Install k6'

          - script: pip install -r prometheus/requirements.txt
            displayName: 'Install dependencies'

          - script: |
              cd prometheus/install/docker
              docker-compose up -d
              sleep 10
            displayName: 'Start Prometheus'

          - script: |
              cd prometheus
              python3 -m tests.cli run --type load --platform docker --k6-vus 20 --k6-duration 10m
            displayName: 'Run load tests'

          - script: |
              cd prometheus/install/docker
              docker-compose down -v
            displayName: 'Cleanup'
            condition: always()
```


---

## Best Practices

### 1. Use Appropriate Test Types for Each Stage

| Pipeline Stage | Recommended Tests | Duration |
|----------------|-------------------|----------|
| PR Validation | Sanity | ~1 min |
| Merge to Main | Sanity, Integration | ~5 min |
| Nightly Build | Sanity, Integration, Load | ~30 min |
| Release | All enabled tests | ~2 hours |

### 2. Configure Timeouts

Always set appropriate timeouts to prevent hung pipelines:

```bash
python3 -m tests.cli run --type load --timeout 1800  # 30 minutes
```

### 3. Use Fail-Fast for PR Validation

Stop on first failure to get faster feedback:

```bash
python3 -m tests.cli run --type sanity --fail-fast
```

### 4. Archive Test Results

Always archive test results for debugging:

```yaml
# GitHub Actions
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: test-results
    path: prometheus/results/
```

### 5. Clean Up Resources

Always clean up test resources, even on failure:

```yaml
# GitHub Actions
- name: Cleanup
  if: always()
  run: python3 -m tests.cli cleanup --platform docker --force
```

### 6. Use Environment-Specific Configurations

Create separate configs for CI:

```yaml
# tests/config/ci.yaml
test:
  name: "ci-tests"
  platform: "docker"

sanity:
  enabled: true
  timeout: 30s

load:
  enabled: true
  duration: 5m
  k6:
    vus: 10
```

```bash
python3 -m tests.cli run --config tests/config/ci.yaml
```

### 7. Parallel Test Execution

Run independent tests in parallel:

```bash
python3 -m tests.cli run --parallel --type sanity --type security
```

---

## Exit Codes

The CLI returns appropriate exit codes for CI/CD:

| Exit Code | Meaning |
|-----------|---------|
| 0 | All tests passed |
| 1 | One or more tests failed |
| 2 | Configuration error |
| 3 | Prometheus unreachable |
| 4 | Timeout exceeded |

---

## Notifications

### Slack Notification (GitHub Actions)

```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    fields: repo,message,commit,author,action,eventName,ref,workflow
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Email Notification (Jenkins)

```groovy
post {
    failure {
        emailext(
            subject: "Prometheus Tests Failed",
            body: "Check ${env.BUILD_URL}",
            recipientProviders: [developers()]
        )
    }
}
```

---

## Scheduled Testing

### Daily Load Tests (GitHub Actions)

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

### Weekly Full Suite (GitLab CI)

```yaml
full-test-suite:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  script:
    - python3 -m tests.cli run --platform minikube
```
