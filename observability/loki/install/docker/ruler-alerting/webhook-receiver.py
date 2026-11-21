#!/usr/bin/env python3
"""Simple webhook receiver — prints Alertmanager alerts to stdout."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            alerts = json.loads(body)
            for alert in alerts:
                status = alert.get("status", "unknown")
                name = alert.get("labels", {}).get("alertname", "?")
                severity = alert.get("labels", {}).get("severity", "?")
                summary = alert.get("annotations", {}).get("summary", "")
                print(
                    f"[{datetime.now().isoformat()}] [{status.upper()}] [{severity}] {name}: {summary}",
                    flush=True,
                )
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Parse error: {e}", flush=True)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print("Webhook receiver listening on :5001", flush=True)
    HTTPServer(("0.0.0.0", 5001), Handler).serve_forever()
