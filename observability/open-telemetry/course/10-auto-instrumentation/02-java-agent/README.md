# Lesson 02-java-agent — Java Agent Auto-Instrumentation

This sub-lesson demonstrates zero-code instrumentation of a Java application using the official `opentelemetry-javaagent.jar` (v2.31.1).

---

## 1. How It Works

The Java Agent uses the JVM's `java.lang.instrument` API and ByteBuddy to dynamically rewrite bytecode when classes are loaded. It automatically intercepts HTTP handlers, servlet containers, JDBC database calls, and gRPC clients.

---

## 2. Compiling the Application

```bash
# Package the plain application JAR
mvn clean package
```

---

## 3. Running with the Java Agent

```bash
# 1. Download the latest official agent JAR (if not already downloaded)
curl -L -O https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v2.31.1/opentelemetry-javaagent.jar

# 2. Run the application with the agent attached
java -javaagent:./opentelemetry-javaagent.jar \
     -Dotel.service.name=auto-java-service \
     -Dotel.traces.exporter=logging \
     -Dotel.metrics.exporter=none \
     -Dotel.logs.exporter=none \
     -jar target/plain-java-server-1.0.0.jar
```

---

## 4. Trigger Requests

```bash
curl http://localhost:8086/orders
```

**Result:**
The console prints formatted OTel spans with full HTTP attributes and timing, without a single line of OpenTelemetry code in the Java codebase.
