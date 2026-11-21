#!/usr/bin/env python3
"""
Simple webhook receiver for testing AlertManager notifications locally.
Run this on your Mac to see alerts come through.

Usage:
    python3 webhook-receiver.py

Listens on port 5001 and prints alert payloads to stdout.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body.decode('utf-8')

        # Determine channel from path
        channel = self.path.strip('/')

        print(f"\n{'='*60}")
        print(f"⚠️  ALERT RECEIVED at {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Channel: {channel}")
        print(f"{'='*60}")

        if isinstance(payload, dict) and 'alerts' in payload:
            for alert in payload['alerts']:
                status = alert.get('status', 'unknown')
                labels = alert.get('labels', {})
                annotations = alert.get('annotations', {})

                icon = "🔴" if status == "firing" else "✅"
                print(f"\n{icon} [{status.upper()}] {labels.get('alertname', 'unknown')}")
                print(f"   Severity:  {labels.get('severity', 'n/a')}")
                print(f"   Service:   {labels.get('service', 'n/a')}")
                print(f"   Cluster:   {labels.get('cluster', 'n/a')}")
                print(f"   Team:      {labels.get('team', 'n/a')}")
                print(f"   Summary:   {annotations.get('summary', 'n/a')}")
                print(f"   Detail:    {annotations.get('description', 'n/a')}")
        else:
            print(json.dumps(payload, indent=2) if isinstance(payload, dict) else payload)

        print(f"{'='*60}\n")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def log_message(self, format, *args):
        # Suppress default HTTP logs to keep output clean
        pass


if __name__ == '__main__':
    port = 5001
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    print(f"🎯 Webhook receiver listening on http://localhost:{port}")
    print(f"   Waiting for AlertManager notifications...")
    print(f"   Endpoints:")
    print(f"     POST /webhook          → default alerts")
    print(f"     POST /webhook/opsgenie → OpsGenie-bound alerts")
    print(f"     POST /webhook/teams    → Teams-bound alerts")
    print(f"\n   Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down webhook receiver")
        server.shutdown()
