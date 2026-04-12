with open("src/aho/dashboard/server.py", "r") as f:
    content = f.read()

# Add import for render_council_svg
content = content.replace("from aho.council.status import collect_status", "from aho.council.status import collect_status\nfrom aho.dashboard.lego.renderer import render_council_svg")

new_routes = """            elif self.path == "/api/lego":
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
            elif self.path == "/components.yaml":"""

content = content.replace('            elif self.path == "/components.yaml":', new_routes)

with open("src/aho/dashboard/server.py", "w") as f:
    f.write(content)
