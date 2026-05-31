{
  "mcpServers": {
    "firebase-tools": {
      "command": "firebase",
      "args": ["mcp"],
      "type": "stdio"
    },
    "context7": {
      "command": "context7-mcp",
      "args": [],
      "type": "stdio"
    },
    "firecrawl": {
      "command": "firecrawl-mcp",
      "args": [],
      "type": "stdio",
      "env": {
        "FIRECRAWL_API_KEY": ""
      }
    },
    "playwright": {
      "command": "playwright-mcp",
      "args": [],
      "type": "stdio"
    },
    "dart": {
      "command": "dart",
      "args": ["mcp-server"],
      "type": "stdio"
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["{{PROJECT_ROOT}}"],
      "type": "stdio"
    },
    "memory": {
      "command": "mcp-server-memory",
      "args": [],
      "type": "stdio"
    },
    "sequential-thinking": {
      "command": "mcp-server-sequential-thinking",
      "args": [],
      "type": "stdio"
    },
    "everything": {
      "command": "mcp-server-everything",
      "args": [],
      "type": "stdio"
    }
  }
}
