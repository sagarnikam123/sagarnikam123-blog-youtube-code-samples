#!/usr/bin/env python3
"""
Main entry point for running the Prometheus Testing Framework CLI as a module.

Usage:
    python3 -m tests run --platform minikube
    python3 -m tests report --input results/test_report.json --format html
    python3 -m tests cleanup --platform docker
    python3 -m tests info
    python3 -m tests status --prometheus-url http://localhost:9090

Requirements: 10.2, 10.4, 10.8
"""

from .cli import main

if __name__ == "__main__":
    main()
