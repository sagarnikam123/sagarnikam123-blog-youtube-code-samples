from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class PlainHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode("utf-8"))
        elif self.path == "/orders":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([{"id": 1, "item": "laptop"}, {"id": 2, "item": "phone"}]).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8085):
    server = HTTPServer(("0.0.0.0", port), PlainHandler)
    print(f"Plain HTTP server running on port {port} (Zero OTel code!)...")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
