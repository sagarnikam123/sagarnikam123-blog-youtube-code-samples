# SkyWalking Java Agent Integration Guide

Integrate SkyWalking Java Agent natively with Java apps across EKS namespaces. The agent collects traces, metrics (JVM), and logs — sending everything through Satellite to OAP.

## Why Native Agent over OTel SDK?

> **Ref:** [Service Agent Overview](https://skywalking.apache.org/docs/main/next/en/concepts-and-designs/service-agent/), [Agent Compatibility](https://skywalking.apache.org/docs/main/next/en/setup/service-agent/agent-compatibility/)

| Feature | SkyWalking Java Agent | OTel SDK + OTel Collector |
|---------|----------------------|--------------------------|
| Traces in SkyWalking UI | Full support (topology, service map, endpoint metrics) | Zipkin Lens only (`/zipkin`) |
| JVM Metrics | Auto-collected (heap, GC, thread, CPU) | Manual instrumentation |
| Log Collection | gRPC reporter (logback/log4j2 toolkit) | Separate log pipeline needed |
| Code Changes | Zero (bytecode instrumentation) | SDK initialization code required |
| Distributed Tracing | `sw8` header propagation (auto) | W3C TraceContext (auto) |
| Profiling | Supported (trace/continuous profiling) | Not available |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Any Namespace (abcd, mnop, pqrs, etc.)                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Java App Pod                                                       │    │
│  │                                                                     │    │
│  │  ┌──────────────────┐  ┌──────────────────────────────────────┐    │    │
│  │  │  Init Container   │  │  Main Container (Java App)           │    │    │
│  │  │  (copies agent)   │  │                                      │    │    │
│  │  │                   │  │  -javaagent:/sky/agent/sw-agent.jar  │    │    │
│  │  │  /skywalking/agent│  │                                      │    │    │
│  │  │       ↓           │  │  Auto-instruments:                   │    │    │
│  │  │  /sky/agent/      │  │  - HTTP (Spring MVC, RestTemplate)   │    │    │
│  │  └──────────────────┘  │  - DB (JDBC, Redis, MongoDB)         │    │    │
│  │         emptyDir       │  - MQ (Kafka, RabbitMQ)              │    │    │
│  │         (shared)       │  - gRPC, Dubbo, etc.                 │    │    │
│  │                        │                                      │    │    │
│  │                        │  Sends via gRPC (:11800):            │    │    │
│  │                        │  ├─ Traces (native protocol)         │    │    │
│  │                        │  ├─ JVM Metrics (auto)               │    │    │
│  │                        │  └─ Logs (gRPC reporter)             │    │    │
│  │                        └──────────────┬───────────────────────┘    │    │
│  └───────────────────────────────────────┼───────────────────────────┘    │
│                                          │                                │
└──────────────────────────────────────────┼────────────────────────────────┘
                                           │ gRPC (11800)
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  skywalking namespace                                                       │
│                                                                             │
│  ┌──────────────┐       ┌──────────────┐       ┌────────────────────┐      │
│  │  Satellite    │──────▶│    OAP       │──────▶│   BanyanDB         │      │
│  │  (x2)        │       │   (x3)       │       │   (cluster)        │      │
│  │  :11800      │       │   :11800     │       └────────────────────┘      │
│  └──────────────┘       └──────┬───────┘                                   │
│                                │                                            │
│  Satellite proxies:            │  OAP processes:                            │
│  - native-tracing    ─────────▶  - Traces → topology, metrics              │
│  - native-log        ─────────▶  - Logs → searchable, correlated           │
│  - native-jvm        ─────────▶  - JVM metrics → instance dashboard        │
│  - native-meter      ─────────▶  - Custom metrics                          │
│  - native-management ─────────▶  - Service/instance registration           │
│  - native-cds        ─────────▶  - Dynamic config                          │
│  - native-profile    ─────────▶  - Profiling data                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Collected by Java Agent

| Data Type | Collection | Code Change? | Visible In UI |
|-----------|-----------|-------------|---------------|
| Traces | Automatic (bytecode instrumentation) | None | General Service → Trace |
| JVM Metrics | Automatic (heap, GC, threads, CPU) | None | General Service → Instance → JVM |
| Topology | Automatic (from trace spans) | None | General Service → Topology |
| Endpoint Metrics | Automatic (latency, throughput, error rate) | None | General Service → Endpoint |
| Logs to SkyWalking | gRPC reporter appender | Yes (pom.xml + logback/log4j2 xml) | General Service → Log |
| Trace ID in stdout | Toolkit layout class | Yes (pom.xml + logback/log4j2 xml) | Fluent Bit → Loki → Grafana |

> **Important:** Traces, JVM metrics, topology, and endpoint metrics work with zero code changes in all three approaches. Log collection requires adding the toolkit Maven dependency and configuring the logging framework — see [Log Collection Setup](#log-collection-setup) below. This applies equally to Approach 1, 2, and 3.

---

## Install SWCK Operator (Prerequisite for Approach 1)

The SkyWalking Cloud on Kubernetes (SWCK) operator provides the mutating webhook that auto-injects the Java agent into pods. It installs into the `skywalking-swck-system` namespace.

> **Ref:** [SWCK Operator](https://skywalking.apache.org/docs/skywalking-swck/next/operator/), [Java Agent Injector](https://skywalking.apache.org/docs/skywalking-swck/next/java-agent-injector/)

### Prerequisites

- cert-manager must be installed in the cluster (for webhook TLS certificates)
- `kubectl` access with cluster-admin privileges

### Check if cert-manager is installed

```bash
kubectl get crd certificates.cert-manager.io
# If not installed, install cert-manager first:
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.2/cert-manager.yaml
kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=120s
```

### Install SWCK Operator

```bash
# Download the latest SWCK release binary (v0.9.0)
SWCK_VERSION=0.9.0
wget https://downloads.apache.org/skywalking/swck/${SWCK_VERSION}/skywalking-swck-${SWCK_VERSION}-bin.tgz

# Extract
tar -xzf skywalking-swck-${SWCK_VERSION}-bin.tgz

# Apply the operator bundle (CRDs + controller + RBAC + webhook)
# This creates the skywalking-swck-system namespace automatically
kubectl apply -f skywalking-swck-${SWCK_VERSION}-bin/config/operator-bundle.yaml
```

### Verify

```bash
# Check operator pod is running
kubectl get pods -n skywalking-swck-system
# Expected:
# NAME                                                  READY   STATUS    RESTARTS   AGE
# skywalking-swck-controller-manager-xxxxx              2/2     Running   0          30s

# Check CRDs are installed
kubectl get crd | grep skywalking
# Expected: swagents.operator.skywalking.apache.org, javaagents.operator.skywalking.apache.org, etc.

# Check mutating webhook is registered
kubectl get mutatingwebhookconfiguration | grep skywalking
# Expected: skywalking-swck-mutating-webhook-configuration
```

### Uninstall SWCK Operator

```bash
# Delete the operator bundle
kubectl delete -f skywalking-swck-${SWCK_VERSION}-bin/config/operator-bundle.yaml

# Or manually if you don't have the bundle file:
kubectl delete mutatingwebhookconfiguration skywalking-swck-mutating-webhook-configuration --ignore-not-found
kubectl delete validatingwebhookconfiguration skywalking-swck-validating-webhook-configuration --ignore-not-found
kubectl delete namespace skywalking-swck-system --ignore-not-found

# Delete CRDs (only if no other SWCK installations)
kubectl delete crd banyandbs.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd fetchers.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd javaagents.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd oapserverconfigs.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd oapserverdynamicconfigs.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd oapservers.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd satellites.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd storages.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd swagents.operator.skywalking.apache.org --ignore-not-found
kubectl delete crd uis.operator.skywalking.apache.org --ignore-not-found
```

### Troubleshooting SWCK Operator

```bash
# Check operator logs
kubectl logs -n skywalking-swck-system -l control-plane=controller-manager --tail=50

# If webhook fails with certificate errors, check cert-manager
kubectl get certificate -n skywalking-swck-system
kubectl get certificaterequest -n skywalking-swck-system

# If pods aren't being injected, verify:
# 1. Namespace has label: kubectl get ns <namespace> --show-labels | grep swck-injection
# 2. Pod has label: kubectl get pod <pod> -o jsonpath='{.metadata.labels.swck-java-agent-injected}'
# 3. SwAgent CR exists: kubectl get swagent -n <namespace>
```

---

## Three Approaches to Integrate

### Approach 1: SWCK Operator Auto-Injection (Recommended)

Zero code changes. The SWCK operator injects the agent via mutating webhook at pod creation time.

> **Ref:** [Java Agent Injector](https://skywalking.apache.org/docs/skywalking-swck/next/java-agent-injector/), [Containerization (K8s)](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/containerization/#kubernetes)

**Best for:** Namespaces where you control deployments and can add labels.

#### Prerequisites
- SWCK Operator installed (see [Install SWCK Operator](#install-swck-operator-prerequisite-for-approach-1) above)
- cert-manager installed in the cluster (required by SWCK for webhook TLS)

#### Steps for a New Namespace

```bash
# 1. Label the namespace
kubectl label namespace <namespace> swck-injection=enabled

# 2. Create SwAgent CR in the target namespace
cat <<EOF | kubectl apply -f -
apiVersion: operator.skywalking.apache.org/v1alpha1
kind: SwAgent
metadata:
  name: swagent-java
  namespace: <namespace>
spec:
  selector: {}
  containerMatcher: ".*"
  javaSidecar:
    name: inject-skywalking-agent
    image: apache/skywalking-java-agent:9.3.0-java21
    env:
      - name: SW_AGENT_COLLECTOR_BACKEND_SERVICES
        value: "skywalking-satellite.skywalking.svc:11800"
      - name: SW_AGENT_NAME
        valueFrom:
          fieldRef:
            fieldPath: metadata.labels['app.kubernetes.io/name']
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 100m
        memory: 128Mi
  sharedVolumeName: sky-agent
EOF

# 3. Add injection label to each deployment
kubectl patch deployment <deploy-name> -n <namespace> --type='json' \
  -p='[{"op": "add", "path": "/spec/template/metadata/labels/swck-java-agent-injected", "value": "true"}]'

# 4. Pods will restart automatically with the agent injected
```

#### What Happens Under the Hood

1. Pod creation request hits K8s API server
2. Mutating webhook intercepts → sends to SWCK operator
3. SWCK checks: namespace label `swck-injection=enabled` + pod label `swck-java-agent-injected=true`
4. Operator mutates pod spec:
   - Adds init container `inject-skywalking-agent` (copies agent JARs to shared volume)
   - Adds `emptyDir` volume `sky-agent`
   - Sets `JAVA_TOOL_OPTIONS=-javaagent:/sky/agent/skywalking-agent.jar` on app containers
   - Sets `SW_AGENT_COLLECTOR_BACKEND_SERVICES` and `SW_AGENT_NAME` from SwAgent CR

#### Agent Image Selection

| Java Version | Agent Image |
|-------------|-------------|
| Java 8 | `apache/skywalking-java-agent:9.3.0-java8` |
| Java 11 | `apache/skywalking-java-agent:9.3.0-java11` |
| Java 17 | `apache/skywalking-java-agent:9.3.0-java17` |
| Java 21 | `apache/skywalking-java-agent:9.3.0-java21` |

> **Ref:** [Docker Hub - skywalking-java-agent](https://hub.docker.com/r/apache/skywalking-java-agent/tags), [Java Agent Setup](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/readme/)

> **What you get out of the box:** Traces, JVM metrics, topology, and endpoint metrics — zero code changes. To also collect logs with traceId (either in stdout or via gRPC to SkyWalking), see [Log Collection Setup](#log-collection-setup).

---

### Approach 2: Init Container Sidecar (No Operator)

Same pattern as SWCK but done manually in the Deployment spec. No operator needed.

> **Ref:** [Containerization (K8s)](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/containerization/#kubernetes)

**Best for:** Namespaces where you can't install SWCK, or want explicit control in manifests.

#### Deployment Patch

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-java-app
  namespace: <namespace>
spec:
  template:
    spec:
      # Init container copies agent to shared volume
      initContainers:
        - name: inject-skywalking-agent
          image: apache/skywalking-java-agent:9.3.0-java21
          command: ["sh"]
          args: ["-c", "mkdir -p /sky/agent && cp -r /skywalking/agent/* /sky/agent"]
          volumeMounts:
            - name: sky-agent
              mountPath: /sky/agent
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi

      containers:
        - name: my-java-app
          image: my-registry/my-java-app:latest
          env:
            - name: JAVA_TOOL_OPTIONS
              value: "-javaagent:/sky/agent/skywalking-agent.jar"
            - name: SW_AGENT_NAME
              value: "my-java-app"
            - name: SW_AGENT_COLLECTOR_BACKEND_SERVICES
              value: "skywalking-satellite.skywalking.svc:11800"
          volumeMounts:
            - name: sky-agent
              mountPath: /sky/agent

      volumes:
        - name: sky-agent
          emptyDir: {}
```

#### Kustomize Patch (for multiple deployments)

Create a strategic merge patch to apply to all Java deployments:

```yaml
# skywalking-agent-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: placeholder  # will be overridden by kustomize
spec:
  template:
    spec:
      initContainers:
        - name: inject-skywalking-agent
          image: apache/skywalking-java-agent:9.3.0-java21
          command: ["sh"]
          args: ["-c", "mkdir -p /sky/agent && cp -r /skywalking/agent/* /sky/agent"]
          volumeMounts:
            - name: sky-agent
              mountPath: /sky/agent
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
      volumes:
        - name: sky-agent
          emptyDir: {}
```

Then in each deployment, add the env vars and volume mount to the app container.

> **What you get out of the box:** Same as Approach 1 — traces, JVM metrics, topology, and endpoint metrics with zero code changes. For log collection with traceId, see [Log Collection Setup](#log-collection-setup).

---

### Approach 3: Bake Agent into Docker Image

Agent is included in the Docker image itself. No init containers or shared volumes.

> **Ref:** [Containerization (Docker)](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/containerization/#docker)

**Best for:** CI/CD pipelines where you control the Dockerfile, or when you need custom agent plugins.

#### Dockerfile

```dockerfile
FROM eclipse-temurin:21-jre

# Download and extract SkyWalking Java Agent
ARG SW_AGENT_VERSION=9.3.0
RUN mkdir -p /opt/skywalking \
    && wget -qO- https://archive.apache.org/dist/skywalking/java-agent/${SW_AGENT_VERSION}/apache-skywalking-java-agent-${SW_AGENT_VERSION}.tgz \
    | tar xz -C /opt/skywalking --strip-components=1

# Copy your application
COPY target/my-app.jar /app/my-app.jar

# Set agent as JVM argument
ENV JAVA_TOOL_OPTIONS="-javaagent:/opt/skywalking/skywalking-agent/skywalking-agent.jar"
ENV SW_AGENT_COLLECTOR_BACKEND_SERVICES="skywalking-satellite.skywalking.svc:11800"

ENTRYPOINT ["java", "-jar", "/app/my-app.jar"]
```

#### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-java-app
spec:
  template:
    spec:
      containers:
        - name: my-java-app
          image: my-registry/my-java-app:latest
          env:
            - name: SW_AGENT_NAME
              value: "my-java-app"
            # Override backend if needed (already set in Dockerfile)
            - name: SW_AGENT_COLLECTOR_BACKEND_SERVICES
              value: "skywalking-satellite.skywalking.svc:11800"
```

---

## Log Collection Setup

The Java agent auto-collects traces and JVM metrics with zero code changes. Logs require a small config change: add the gRPC log reporter appender to your logging framework config.

> **Ref:** [Log Collection via Agents](https://skywalking.apache.org/docs/main/next/en/setup/backend/log-agent-native/), [Logback Toolkit](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/application-toolkit-logback-1.x/), [Log4j2 Toolkit](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/application-toolkit-log4j-2.x/)

### How It Works

```
Java App (logback/log4j2)
    │
    ├─ Console Appender → stdout → Fluent Bit → Loki/Grafana (existing flow)
    │   (with trace ID injected by agent toolkit)
    │
    └─ GRPCLogClientAppender → gRPC → Satellite → OAP → BanyanDB → SkyWalking UI
        (trace ID, segment ID, span ID auto-attached)
```

The agent's log toolkit does two things:
1. Injects trace context (`traceId`, `segmentId`, `spanId`) into log entries
2. Sends logs via gRPC to the backend (Satellite → OAP) for correlation in SkyWalking UI

### Option A: Logback (most common for Spring Boot)

#### 1. Add Dependency

Maven:
```xml
<dependency>
    <groupId>org.apache.skywalking</groupId>
    <artifactId>apm-toolkit-logback-1.x</artifactId>
    <version>9.3.0</version>
</dependency>
```

Gradle:
```groovy
implementation 'org.apache.skywalking:apm-toolkit-logback-1.x:9.3.0'
```

#### 2. Update logback.xml (or logback-spring.xml)

```xml
<configuration>
    <!-- Existing console appender with trace ID -->
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
            <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout">
                <Pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{tid}] [%thread] %-5level %logger{36} - %msg%n</Pattern>
            </layout>
        </encoder>
    </appender>

    <!-- gRPC log reporter — sends logs to Satellite/OAP -->
    <appender name="grpc-log" class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.log.GRPCLogClientAppender">
        <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
            <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout">
                <Pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{tid}] [%thread] %-5level %logger{36} - %msg%n</Pattern>
            </layout>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
        <appender-ref ref="grpc-log"/>
    </root>
</configuration>
```

#### 3. (Recommended) Wrap with AsyncAppender for Production

The `GRPCLogClientAppender` sends logs via gRPC which involves network I/O. To prevent logging from blocking your application's main thread, wrap it with Logback's `AsyncAppender`:

```xml
<configuration>
    <!-- Console appender with trace ID -->
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
            <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout">
                <Pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{tid}] [%thread] %-5level %logger{36} - %msg%n</Pattern>
            </layout>
        </encoder>
    </appender>

    <!-- gRPC log reporter — sends logs to Satellite/OAP -->
    <appender name="grpc-log" class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.log.GRPCLogClientAppender">
        <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
            <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout">
                <Pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{tid}] [%thread] %-5level %logger{36} - %msg%n</Pattern>
            </layout>
        </encoder>
    </appender>

    <!-- Async wrapper for non-blocking gRPC logging -->
    <appender name="async-grpc-log" class="ch.qos.logback.classic.AsyncAppender">
        <discardingThreshold>0</discardingThreshold>  <!-- Don't discard any logs (0 = keep all) -->
        <queueSize>1024</queueSize>                   <!-- Buffer size for queued logs -->
        <neverBlock>true</neverBlock>                 <!-- Don't block app if queue is full -->
        <appender-ref ref="grpc-log"/>
    </appender>

    <root level="INFO">
        <appender-ref ref="STDOUT"/>
        <appender-ref ref="async-grpc-log"/>
    </root>
</configuration>
```

**What AsyncAppender does:**
- Queues log events in memory and writes them via a background thread
- Prevents gRPC network latency from blocking your application's request handling
- `neverBlock=true` ensures the app never waits if the queue is full (logs may be dropped under extreme load)
- `discardingThreshold=0` keeps all log levels (default discards DEBUG/TRACE when queue is 80% full)

> **Ref:** [Logback AsyncAppender](https://logback.qos.ch/manual/appenders.html#AsyncAppender)

#### 1. Add Dependency

Maven:
```xml
<dependency>
    <groupId>org.apache.skywalking</groupId>
    <artifactId>apm-toolkit-log4j-2.x</artifactId>
    <version>9.3.0</version>
</dependency>
```

Gradle:
```groovy
implementation 'org.apache.skywalking:apm-toolkit-log4j-2.x:9.3.0'
```

#### 2. Update log4j2.xml

```xml
<Configuration>
    <Appenders>
        <!-- Existing console appender with trace ID -->
        <Console name="Console" target="SYSTEM_OUT">
            <PatternLayout pattern="%d [%traceId] %-5p %c{1}:%L - %m%n"/>
        </Console>

        <!-- gRPC log reporter — sends logs to Satellite/OAP -->
        <GRPCLogClientAppender name="grpc-log">
            <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
        </GRPCLogClientAppender>
    </Appenders>

    <Loggers>
        <Root level="INFO">
            <AppenderRef ref="Console"/>
            <AppenderRef ref="grpc-log"/>
        </Root>
    </Loggers>
</Configuration>
```

#### 3. (Recommended) Use Async Logger for Production

Log4j2 has built-in async logging support. For non-blocking gRPC log reporting, use `AsyncLogger`:

```xml
<Configuration>
    <Appenders>
        <Console name="Console" target="SYSTEM_OUT">
            <PatternLayout pattern="%d [%traceId] %-5p %c{1}:%L - %m%n"/>
        </Console>

        <GRPCLogClientAppender name="grpc-log">
            <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
        </GRPCLogClientAppender>
    </Appenders>

    <Loggers>
        <!-- Use AsyncLogger for non-blocking logging -->
        <AsyncRoot level="INFO">
            <AppenderRef ref="Console"/>
            <AppenderRef ref="grpc-log"/>
        </AsyncRoot>
    </Loggers>
</Configuration>
```

Or wrap with `Async` appender:

```xml
<Appenders>
    <GRPCLogClientAppender name="grpc-log">
        <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
    </GRPCLogClientAppender>

    <Async name="async-grpc-log">
        <AppenderRef ref="grpc-log"/>
    </Async>
</Appenders>
```

> **Ref:** [Log4j2 Async Loggers](https://logging.apache.org/log4j/2.x/manual/async.html)

### No Logging Framework Changes? (Trace ID in stdout only)

If you don't want to send logs via gRPC but still want trace IDs in your console output for Fluent Bit → Loki correlation, just add the toolkit dependency. The agent's activation JAR (`apm-toolkit-logback-1.x-activation.jar` in the agent's `activations/` folder) auto-injects trace context into MDC — no `GRPCLogClientAppender` needed.

The `%X{tid}` or `%traceId` pattern will output the trace ID. Without the agent running, it prints `TID: N/A`.

---

## Profiling Setup

The Java agent supports two types of in-process profiling, both delivered as on-demand tasks from OAP via the UI. No code changes needed — the agent handles everything. Profiling data flows through Satellite just like traces.

> **Ref:** [Trace Profiling](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-trace-profiling/), [Java App Profiling (Async Profiler)](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-java-app-profiling/)

### Profiling Types

| Type | What It Does | When to Use | Agent Support |
|------|-------------|-------------|---------------|
| Trace Profiling | Periodically samples thread stacks for a specific slow endpoint | Endpoint has high latency, need to find which code line is slow | Built-in (always available) |
| Async Profiler (Java App Profiling) | Uses AsyncProfiler (bundled in agent) for CPU, memory allocation, and lock profiling | CPU spikes, memory pressure, lock contention | Built-in (agent 9.x+) |

> Continuous Profiling uses eBPF via SkyWalking Rover — not the Java agent. It's a separate component and not covered here.

### How It Works

```
SkyWalking UI (create profiling task)
        │
        ▼
    OAP Server (stores task, notifies agent via CDS (Configuration Discovery Service) protocol)
        │
        ▼ (agent polls for tasks)
    Java Agent (receives task, starts profiling)
        │
        ├─ Trace Profiling: samples thread stacks periodically
        │   during matching endpoint requests
        │
        └─ Async Profiler: starts AsyncProfiler, collects JFR (Java Flight Recorder) data
            for CPU/ALLOC/LOCK events
        │
        ▼ gRPC (11800)
    Satellite (proxies profiling data)
        │
        ▼
    OAP Server (stores + analyzes → flame graph)
        │
        ▼
    SkyWalking UI (view flame graph / thread stack analysis)
```

### Step 1: Enable Profiling Receivers in OAP

Add these to `values.yaml` under `oap.env`:

```yaml
    # Trace Profiling Receiver — accepts thread stack sampling data from agents
    SW_RECEIVER_PROFILE: "default"

    # Async Profiler Receiver — accepts JFR data (CPU/ALLOC/LOCK) from agents
    SW_RECEIVER_ASYNC_PROFILER: "default"
```

Then upgrade the Helm release:

```bash
helm upgrade skywalking oci://registry-1.docker.io/apache/skywalking-helm \
  --version 4.8.0 \
  -n skywalking \
  -f environments/scnx-global-dev-aps1-eks/values.yaml
```

### Step 2: No Agent Changes Needed

Both profiling features are built into the Java agent and enabled by default. The agent:
- Connects to Satellite on `skywalking-satellite.skywalking.svc:11800`
- Polls OAP (via Satellite) for profiling tasks using the CDS (Configuration Discovery Service) protocol
- When a task is received, starts profiling and uploads results

Satellite already has the required receiver/forwarder plugins:

| Data | Satellite Receiver | Satellite Forwarder |
|------|-------------------|-------------------|
| Trace Profiling | `grpc-native-profile-receiver` | `native-profile-grpc-forwarder` |
| Async Profiler | `grpc-native-async-profiler-receiver` | `native-async-profiler-grpc-forwarder` |

### Step 3: Create Profiling Tasks from UI

#### Trace Profiling

1. Go to SkyWalking UI → select a service → Trace Profiling tab
2. Create a new task:
   - Endpoint: the slow endpoint (e.g., `POST:/api/v1/search`)
   - Duration: how long to run the task (e.g., 5 minutes)
   - Min Duration Threshold: only profile requests slower than this (e.g., 500ms)
   - Dump Period: thread stack sampling interval (e.g., 10ms)
   - Max Sampling Count: limit to prevent overhead (e.g., 5)
3. Generate traffic to the endpoint
4. View results: select a profiled trace → analyze thread stack → find the slow code line

#### Async Profiler (Java App Profiling)

1. Go to SkyWalking UI → select a service → Async Profiler tab
2. Create a new task:
   - Instances: select which instances to profile
   - Duration: sampling duration (e.g., 30 seconds)
   - Events: select what to profile
     - `CPU` / `WALL` / `ITIMER` / `CTIMER` — CPU cycles
     - `ALLOC` — Java heap allocations
     - `LOCK` — contended lock attempts (monitors + ReentrantLocks)
   - Exec Args: optional AsyncProfiler args (e.g., `alloc=2k,lock=2s`)
3. Wait for the agent to collect and upload JFR data
4. View results: flame graph showing hot code paths

### Profiling Agent Config (Optional Tuning)

These are agent-level settings, set via env vars or `agent.config`. Defaults are fine for most cases:

| Variable | Default | Description |
|----------|---------|-------------|
| `profile.active` | `true` | Enable/disable trace profiling |
| `profile.max_parallel` | `5` | Max concurrent profiling tasks |
| `profile.max_accept_sub_parallel` | `5` | Max sub-tasks per task |
| `profile.duration` | `10` | Max profiling duration (minutes) |
| `profile.dump_max_stack_depth` | `500` | Max thread stack depth to dump |
| `profile.snapshot_transport_buffer_size` | `50` | Buffer size for snapshot transport |

---

## Agent Configuration Reference

Key environment variables (set via SwAgent CR env, Deployment env, or `agent.config`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SW_AGENT_NAME` | `Your_ApplicationName` | Service name shown in UI. Use `fieldRef` to derive from pod label. |
| `SW_AGENT_COLLECTOR_BACKEND_SERVICES` | `127.0.0.1:11800` | Backend address. Set to `skywalking-satellite.skywalking.svc:11800` |
| `SW_AGENT_INSTANCE_NAME` | UUID | Instance name. Auto-generated is fine for K8s. |
| `SW_LOGGING_LEVEL` | `INFO` | Agent's own log level (not app logs). Use `DEBUG` for troubleshooting. |
| `SW_LOGGING_DIR` | `/sky/agent/logs` | Agent log directory. |
| `SW_AGENT_TRACE_IGNORE_PATH` | (empty) | Paths to exclude from tracing (e.g., `/health,/ready`). |

> **Ref:** [Agent Configuration](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/readme/), [Setting Override](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/setting-override/)

### Ignoring Health Check Endpoints

To avoid noisy traces from K8s probes:

```bash
# Via environment variable
SW_AGENT_TRACE_IGNORE_PATH="/health,/ready,/actuator/**,/healthz"
```

Or via SwAgent CR annotation:
```yaml
agent.skywalking.apache.org/agent.trace.ignore_path: "/health,/ready,/actuator/**"
```

> **Ref:** [Trace Ignore Plugin](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/how-to-tolerate-exceptions/)

### Grouping Services by Kubernetes Namespace in UI

By default, all services from all namespaces appear in a flat list in the SkyWalking UI. To group them by K8s namespace, use the service name format `<group>::<service>`. SkyWalking parses the `::` separator and creates groups automatically.

> **Ref:** [Service Auto Grouping](https://skywalking.apache.org/docs/main/next/en/setup/backend/service-auto-grouping/)

**IMPORTANT:** There is NO `SW_AGENT_SERVICE_GROUP` or `SW_AGENT_NAMESPACE` env var for grouping. The group is parsed from the service name itself.

```
Without grouping:                    With grouping:
┌──────────────────────────┐         ┌──────────────────────────┐
│ Services (flat list)     │         │ Services (grouped)       │
│                          │         │                          │
│ jetter-api-service      │         │ Group: sterling              │
│ hector-gpt-service      │         │   jetter-api-service    │
│ monsson-alert-service      │         │   hector-gpt-service    │
│ monolog-ingest-service     │         │                          │
│                          │         │ Group: snypr-alert       │
│                          │         │   monsson-alert-service    │
│                          │         │                          │
│                          │         │ Group: snypr-ingest      │
│                          │         │   monolog-ingest-service   │
└──────────────────────────┘         └──────────────────────────┘
```

#### How It Works

The service name format is: `[group]::[service-name]`

```
Service Name: sterling::jetter-api-service
              ^^^^   ^^^^^^^^^^^^^^^^^^
              group  logical service name
```

OAP parses the `::` and creates:
- Group: `sterling`
- Service: `jetter-api-service`

The GraphQL API supports filtering by group:
```graphql
getAllServices(duration: Duration!, group: "sterling") { ... }
```

#### For SWCK Operator (Approach 1) — Use Pod Annotation

Since Kubernetes `fieldRef` cannot concatenate values (namespace + service name), use a pod annotation to set the full service name with group prefix:

```yaml
# In your Deployment spec (or via kubectl patch)
spec:
  template:
    metadata:
      labels:
        swck-java-agent-injected: "true"
      annotations:
        agent.skywalking.apache.org/agent.service_name: "sterling::jetter-api-service"
```

The annotation overrides `SW_AGENT_NAME` env var. Create one SwAgent CR per namespace (without `SW_AGENT_NAME` env var), then set the service name per deployment via annotation:

```yaml
apiVersion: operator.skywalking.apache.org/v1alpha1
kind: SwAgent
metadata:
  name: swagent-java
  namespace: sterling
spec:
  selector: {}
  containerMatcher: ".*"
  javaSidecar:
    name: inject-skywalking-agent
    image: apache/skywalking-java-agent:9.3.0-java21
    env:
      - name: SW_AGENT_COLLECTOR_BACKEND_SERVICES
        value: "skywalking-satellite.skywalking.svc:11800"
      # DO NOT set SW_AGENT_NAME here — use pod annotation instead
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 100m
        memory: 128Mi
  sharedVolumeName: sky-agent
```

Then patch each deployment:

```bash
kubectl patch deployment jetter-api-service -n sterling --type='json' -p='[
  {"op": "add", "path": "/spec/template/metadata/labels/swck-java-agent-injected", "value": "true"},
  {"op": "add", "path": "/spec/template/metadata/annotations/agent.skywalking.apache.org~1agent.service_name", "value": "sterling::jetter-api-service"}
]'
```

Or batch patch all deployments:

```bash
for deploy in jetter-api-service hector-gpt-service; do
  kubectl patch deployment $deploy -n sterling --type='json' -p="[
    {\"op\": \"add\", \"path\": \"/spec/template/metadata/labels/swck-java-agent-injected\", \"value\": \"true\"},
    {\"op\": \"add\", \"path\": \"/spec/template/metadata/annotations/agent.skywalking.apache.org~1agent.service_name\", \"value\": \"sterling::${deploy}\"}
  ]"
done
```

#### For Init Container (Approach 2) / Dockerfile (Approach 3)

Set `SW_AGENT_NAME` directly with the group prefix:

```yaml
env:
  - name: SW_AGENT_NAME
    value: "sterling::jetter-api-service"
```

#### For Helm Charts (Recommended for Future Deployments)

Add the annotation to your app's Helm `values.yaml`:

```yaml
podAnnotations:
  agent.skywalking.apache.org/agent.service_name: "sterling::my-service-name"

podLabels:
  swck-java-agent-injected: "true"
```

Or in the Deployment template:

```yaml
spec:
  template:
    metadata:
      labels:
        swck-java-agent-injected: "true"
      annotations:
        agent.skywalking.apache.org/agent.service_name: "sterling::{{ .Values.serviceName }}"
```

#### Verify Grouping

```bash
# Check SW_AGENT_NAME has group prefix
kubectl exec -n sterling <pod> -c <container> -- printenv SW_AGENT_NAME
# Expected: sterling::jetter-api-service

# Query via GraphQL
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { services: getAllServices(duration: {start: \"2026-02-24 0000\", end: \"2026-02-24 2359\", step: MINUTE}) { label: name group } }"}' \
  | jq '.data.services[] | select(.group == "sterling")'
```

> **Note:** Old services (without group) remain until TTL expires (default 3 days). New services with `sterling::` prefix appear as separate entries with `group: "sterling"`.

---

## Satellite Configuration

Satellite v1.3.0 (deployed via Helm chart) already supports all native SkyWalking protocols out of the box. The default pipe plugins handle:

> **Ref:** [Satellite Overview](https://skywalking.apache.org/docs/skywalking-satellite/next/readme/), [Satellite Plugins](https://skywalking.apache.org/docs/skywalking-satellite/next/en/setup/configuration/pipe-plugins/)

| Receiver Plugin | Forwarder Plugin | Data |
|----------------|-----------------|------|
| `grpc-native-tracing-receiver` | `native-tracing-grpc-forwarder` | Traces |
| `grpc-native-log-receiver` | `native-log-grpc-forwarder` | Logs (gRPC reporter) |
| `grpc-native-jvm-receiver` | (forwarded with management) | JVM Metrics |
| `grpc-native-meter-receiver` | `native-meter-grpc-forwarder` | Custom Metrics |
| `grpc-native-management-receiver` | `native-management-grpc-forwarder` | Service Registration |
| `grpc-native-profile-receiver` | `native-profile-grpc-forwarder` | Profiling |
| `grpc-native-cds-receiver` | `native-cds-grpc-forwarder` | Dynamic Config |

No Satellite configuration changes needed. Agents connect to `skywalking-satellite.skywalking.svc:11800` and Satellite forwards everything to OAP.

---

## Verification

### Check Agent is Running

```bash
# Check init container completed
kubectl get pod <pod> -n <namespace> -o jsonpath='{.status.initContainerStatuses[?(@.name=="inject-skywalking-agent")].state}'

# Check agent files
kubectl exec -n <namespace> <pod> -c <container> -- ls /sky/agent/skywalking-agent.jar

# Check agent logs
kubectl exec -n <namespace> <pod> -c <container> -- tail -20 /sky/agent/logs/skywalking-api.log

# Check env vars
kubectl exec -n <namespace> <pod> -c <container> -- printenv | grep SW_
```

### Check Data in SkyWalking UI

| What | Where in UI |
|------|-------------|
| Service registered | General Service → Service list |
| Traces flowing | General Service → select service → Trace tab |
| JVM metrics | General Service → select service → Instance → JVM tab |
| Topology | General Service → Topology |
| Logs (if gRPC reporter configured) | General Service → select service → Log tab |
| Endpoint metrics | General Service → select service → Endpoint tab |

### Troubleshooting

```bash
# Agent can't connect to Satellite
kubectl exec -n <namespace> <pod> -c <container> -- cat /sky/agent/logs/skywalking-api.log | grep -i "connect\|error\|fail"

# Check Satellite is receiving data
kubectl logs -n skywalking -l component=satellite --tail=50

# Check OAP is processing
kubectl logs -n skywalking -l component=oap --tail=50 | grep -i "register\|segment"

# DNS resolution test
kubectl exec -n <namespace> <pod> -c <container> -- nslookup skywalking-satellite.skywalking.svc
```

---

## Quick Reference: Which Approach to Use?

| Scenario | Recommended Approach |
|----------|---------------------|
| New namespace, many Java apps | Approach 1 (SWCK) — label namespace + create SwAgent CR |
| Can't install SWCK operator | Approach 2 (Init Container) — add to each Deployment |
| Custom agent plugins needed | Approach 3 (Dockerfile) — full control over agent build |
| Already using SWCK (abcd namespace) | Approach 1 — just add pod labels to new deployments |
| Mixed Java versions in same namespace | Approach 1 with per-pod annotation override for image |
| CI/CD pipeline builds images | Approach 3 — bake agent into image, set env vars in K8s |

## Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| SkyWalking OAP | 10.3.0 | Current deployment |
| SkyWalking Java Agent | 9.3.0 | Compatible with OAP 10.x |
| Satellite | v1.3.0 | Supports all native protocols |
| BanyanDB | 0.9.0 | Storage backend |
| Java | 8, 11, 17, 21 | Agent supports JDK 8-25 |

## References

- [SkyWalking Documentation Home](https://skywalking.apache.org/docs/main/next/readme/)
- [Service Auto Grouping](https://skywalking.apache.org/docs/main/next/en/setup/backend/service-auto-grouping/)
- [SWCK Operator Installation](https://skywalking.apache.org/docs/skywalking-swck/next/operator/)
- [Java Agent Setup](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/readme/)
- [Agent Setting Override](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/setting-override/)
- [Agent Containerization (K8s/Docker)](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/containerization/)
- [SWCK Java Agent Injector](https://skywalking.apache.org/docs/skywalking-swck/next/java-agent-injector/)
- [Logback Toolkit](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/application-toolkit-logback-1.x/)
- [Log4j2 Toolkit](https://skywalking.apache.org/docs/skywalking-java/next/en/setup/service-agent/java-agent/application-toolkit-log4j-2.x/)
- [Log Collection via Agents](https://skywalking.apache.org/docs/main/next/en/setup/backend/log-agent-native/)
- [Trace Profiling](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-trace-profiling/)
- [Java App Profiling (Async Profiler)](https://skywalking.apache.org/docs/main/next/en/setup/backend/backend-java-app-profiling/)
- [Satellite Overview](https://skywalking.apache.org/docs/skywalking-satellite/next/readme/)
- [Satellite Plugins](https://skywalking.apache.org/docs/skywalking-satellite/next/en/setup/configuration/pipe-plugins/)
- [Agent Compatibility](https://skywalking.apache.org/docs/main/next/en/setup/service-agent/agent-compatibility/)
- [Configuration Vocabulary](https://skywalking.apache.org/docs/main/next/en/setup/backend/configuration-vocabulary/)
- [TTL Settings](https://skywalking.apache.org/docs/main/next/en/setup/backend/ttl/)
