"""Dashboard HTTP server.

Serves:
  /api/state  — full aggregated dashboard JSON
  /api/health — legacy health endpoint (traces tail)
  /           — static files from web/claw3d/build/web/ (Flutter app)

Binds to 127.0.0.1 only. No auth. Polling-friendly with 2s cache.
"""
import http.server
import json
from pathlib import Path

from aho.paths import find_project_root
from aho.config import get_dashboard_port
from aho.dashboard.aggregator import get_state


def create_handler(project_root: Path):
    """Create HTTP handler with project root bound."""
    static_dir = project_root / "web" / "claw3d"

    # Prefer built Flutter app if it exists
    build_dir = static_dir / "build" / "web"
    serve_dir = str(build_dir) if build_dir.exists() else str(static_dir)

    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=serve_dir, **kwargs)

        def do_GET(self):
            if self.path == "/api/state":
                self._json_response(get_state())
            elif self.path == "/api/health":
                state = get_state()
                self._json_response({
                    "traces": state.get("traces", []),
                    "count": len(state.get("traces", [])),
                })
            elif self.path == "/components.yaml":
                comp_path = project_root / "artifacts" / "harness" / "components.yaml"
                if comp_path.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(comp_path.read_bytes())
                else:
                    self.send_error(404)
            else:
                super().do_GET()

        def _json_response(self, data):
            body = json.dumps(data, default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            # Suppress per-request logs; dashboard polls every 5s
            pass

    return DashboardHandler


def serve(port: int = None):
    """Start the dashboard HTTP server."""
    root = find_project_root()
    if port is None:
        port = get_dashboard_port()

    handler = create_handler(root)
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    print(f"[aho-dashboard] Listening on http://127.0.0.1:{port}")
    print(f"[aho-dashboard] API: /api/state | Static: /")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[aho-dashboard] Stopped.")
        server.server_close()


if __name__ == "__main__":
    serve()
