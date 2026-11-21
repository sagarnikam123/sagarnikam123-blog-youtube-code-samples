# Lesson 01-samplers-and-processors — Samplers and Span Processors

In this lesson, you will configure and test the behavior of the **`ParentBased`** sampler:

1. **Unparented Root Spans**: Evaluated against the root sampling strategy (configured here as `ALWAYS_OFF`, proving that unparented spans are dropped).
2. **Spans with Remote Sampled Parents**: Evaluated against `remote_parent_sampled` (configured as `ALWAYS_ON`, proving that downstream child spans always inherit the sampling decision of upstream callers).

---

## Running in Python

```bash
cd python
pip install -r requirements.txt
python main.py
```

## Running in Java

```bash
cd java
mvn clean test
```
