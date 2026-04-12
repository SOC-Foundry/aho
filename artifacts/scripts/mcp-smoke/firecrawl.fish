#!/usr/bin/env fish
# mcp-smoke/firecrawl.fish — CLI health check for firecrawl-mcp
# Exit 0 if server responds to JSON-RPC initialize, 1 otherwise
# Note: requires FIRECRAWL_API_KEY env var for actual API calls;
# this smoke only tests protocol handshake, not API functionality

set -l server_name "firecrawl"
echo "[mcp-smoke] testing $server_name CLI invocation"

set -l msg '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}'
set -l response (printf '%s\n' $msg | timeout 5 firecrawl-mcp 2>/dev/null)
# stdio servers stay alive; timeout exit 124 is expected
if string match -q '*"protocolVersion"*' "$response"
    echo "[mcp-smoke] $server_name OK"
    exit 0
else
    echo "[mcp-smoke] $server_name FAIL" >&2
    echo "$response" >&2
    exit 1
end
