# Lesson 01-semconv-span — Semantic Convention Enforcement

In this lesson, you will test and verify compliance with modern stable OpenTelemetry Semantic Conventions (v1.28.0+).

---

## What Is Being Validated

1. **HTTP Server Span**:
   - `http.request.method` = `"GET"`
   - `http.response.status_code` = `200`
   - `url.path` = `"/api/v1/orders"`
   - `server.address` = `"api.internal"`
   - `server.port` = `8080`
2. **Database Client Span**:
   - `db.system` = `"postgresql"`
   - `db.operation` = `"SELECT"`
   - `db.collection.name` = `"orders"`
   - `db.namespace` = `"ecommerce_db"`
3. **Causal Hierarchy**:
   - Child database span `parent_id` equals the HTTP server span's `span_id`.

---

## Running in Python

```bash
cd python
pip install -r requirements.txt
python test_semconv.py
```

## Running in Java

```bash
cd java
mvn clean test
```
