#!/usr/bin/env fish
# mcp-smoke/server-memory.fish — CLI health check for @modelcontextprotocol/server-memory
# Exit 0 if server responds to JSON-RPC initialize, 1 otherwise

set -l server_name "server-memory"
echo "[mcp-smoke] testing $server_name CLI invocation"

set -l msg '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}'
set -l response (printf '%s\n' $msg | timeout 5 mcp-server-memory 2>/dev/null)
# stdio servers stay alive; timeout exit 124 is expected
if string match -q '*"protocolVersion"*' "$response"
    echo "[mcp-smoke] $server_name OK"
    exit 0
else
    echo "[mcp-smoke] $server_name FAIL" >&2
    echo "$response" >&2
    exit 1
end
