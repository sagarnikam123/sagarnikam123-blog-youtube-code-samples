# Lesson 01-broken-pipelines — Diagnosing & Remediating Failures

This lesson walks through two common production bugs and tests automated remediation:

1. **Thread Context Leakage:** Demonstrates an async worker thread creating an orphaned trace due to missing context attachment, and how `context.attach()` remediates it.
2. **Collector Processor Ordering:** Validates why `memory_limiter` must be positioned first in all Collector pipelines.

---

## Running the Diagnostics

```bash
python diagnose.py
```
