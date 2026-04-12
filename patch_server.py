with open("src/aho/dashboard/server.py", "r") as f:
    content = f.read()

new_import = "from aho.dashboard.aggregator import get_state\nfrom aho.council.status import collect_status"
content = content.replace("from aho.dashboard.aggregator import get_state", new_import)

new_route = """            elif self.path == "/api/council":
                # Convert the pydantic model to a dict so _json_response can dump it
                # Or just return its model_dump()
                self._json_response(collect_status().model_dump())
            elif self.path == "/components.yaml":"""

content = content.replace('            elif self.path == "/components.yaml":', new_route)

with open("src/aho/dashboard/server.py", "w") as f:
    f.write(content)
