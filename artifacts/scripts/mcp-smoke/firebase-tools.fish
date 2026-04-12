#!/usr/bin/env fish
# mcp-smoke/firebase-tools.fish — CLI health check for firebase-tools MCP
# Exit 0 if server responds to JSON-RPC initialize, 1 otherwise
# Note: requires `firebase login` for full functionality;
# this smoke tests protocol handshake only

set -l server_name "firebase-tools"
echo "[mcp-smoke] testing $server_name CLI invocation"

set -l msg '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}'
# firebase mcp stays alive after responding (exit 124 from timeout is expected)
set -l response (printf '%s\n' $msg | timeout 5 firebase mcp 2>/dev/null)

if string match -q '*"protocolVersion"*' "$response"
    echo "[mcp-smoke] $server_name OK"
    exit 0
else
    echo "[mcp-smoke] $server_name FAIL" >&2
    echo "$response" >&2
    exit 1
end
