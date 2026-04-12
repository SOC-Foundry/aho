#!/usr/bin/env fish
# mcp-smoke/dart.fish — CLI health check for dart mcp-server (official Dart/Flutter MCP)
# Exit 0 if server responds to JSON-RPC initialize, 1 otherwise
#
# Note: dart mcp-server requires stdin to stay open while it processes.
# We use a subshell with sleep to keep stdin alive for the response.

set -l server_name "dart"
echo "[mcp-smoke] testing $server_name CLI invocation"

set -l msg '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}'
set -l response (begin; echo $msg; sleep 3; end | timeout 5 dart mcp-server 2>/dev/null)

# stdio servers stay alive; timeout exit 124 is expected
if string match -q '*"protocolVersion"*' "$response"
    echo "[mcp-smoke] $server_name OK"
    exit 0
else
    echo "[mcp-smoke] $server_name FAIL" >&2
    echo "$response" >&2
    exit 1
end
