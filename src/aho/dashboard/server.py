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
from aho.dashboard.otel_aggregator import get_otel_state, get_workstream_detail
from aho.council.status import collect_status
from aho.dashboard.lego.renderer import render_council_svg


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
            elif self.path == "/api/otel":
                self._json_response(get_otel_state())
            elif self.path.startswith("/api/otel/workstream/"):
                ws_id = self.path[len("/api/otel/workstream/"):]
                detail = get_workstream_detail(ws_id)
                if detail is None:
                    self.send_error(404, f"Unknown workstream: {ws_id}")
                else:
                    self._json_response(detail)
            elif self.path == "/api/council":
                # Convert the pydantic model to a dict so _json_response can dump it
                # Or just return its model_dump()
                self._json_response(collect_status().model_dump())
            elif self.path == "/api/lego":
                # Returning the exact data shape that generates the SVG
                # It's essentially the council status or a mapped version
                status = collect_status()
                # Expose 'figures' as required by acceptance check
                data = status.model_dump()
                data['figures'] = data['members']
                self._json_response(data)
            elif self.path == "/lego/":
                # Render SVG directly
                svg = render_council_svg(collect_status())
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml")
                self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
                body = svg.encode("utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
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
