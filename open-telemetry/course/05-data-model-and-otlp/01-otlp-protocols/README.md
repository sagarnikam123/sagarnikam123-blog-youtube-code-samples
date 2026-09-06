# Lesson 01-otlp-protocols — OTLP/gRPC vs OTLP/HTTP

This lesson demonstrates exporting telemetry via both standard OpenTelemetry wire protocols:

- **OTLP / gRPC (`localhost:4317`)**: Binary Protobuf framed over HTTP/2 streaming. Preferred for high-volume microservices.
- **OTLP / HTTP (`localhost:4318`)**: Binary Protobuf or JSON requests over HTTP POST (`/v1/traces`). Preferred for environments where gRPC is blocked or inefficient (serverless functions, browser runtimes).

---

## Running in Python

```bash
cd python
pip install -r requirements.txt

# Run gRPC export:
python export_grpc.py

# Run HTTP export:
python export_http.py
```

---

## Running in Java

```bash
cd java

# Run gRPC export:
mvn clean compile exec:java -Dexec.mainClass="com.course.OtlpGrpcExport"

# Run HTTP export:
mvn compile exec:java -Dexec.mainClass="com.course.OtlpHttpExport"
```
