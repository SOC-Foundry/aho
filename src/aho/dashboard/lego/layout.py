from typing import Dict, Tuple

# Base dimensions for elements
BLOCK_W = 180
BLOCK_H = 60

# Positioning logic per node based on Name/Kind
# We map nodes dynamically to columns/rows, but here are predefined logical X columns
COL_EXECUTOR = 50
COL_DAEMON = 350
COL_LLM = 650
COL_MCP = 950
COL_INFRA = 1250

def get_node_position(name: str, kind: str) -> Tuple[int, int]:
    # Returns center x, y for the node
    n = name.lower()
    
    if "openclaw" in n:
        return COL_DAEMON, 150
    elif "nemoclaw" in n:
        return COL_DAEMON, 350
        
    elif "qwen" in n:
        return COL_LLM, 150
    elif "nemotron" in n:
        return COL_LLM, 350
    elif "glm" in n or "evaluator" in n:
        return COL_LLM, 550
        
    elif "mcp" in kind.lower() or "mcp" in n:
        # stack MCPs
        mcp_y_offsets = {
            "mcp-context7": 100,
            "mcp-server-sequential-thinking": 200,
            "mcp-playwright": 300,
            "mcp-server-filesystem": 400,
            "mcp-firebase-tools": 500,
            "mcp-firecrawl": 600,
            "mcp-dart": 700,
            "mcp-server-memory": 800,
            "mcp-server-everything": 900
        }
        y = mcp_y_offsets.get(n, 1000)
        return COL_MCP, y
        
    elif "chromadb" in n or "embed" in n:
        infra_y = 150 if "chroma" in n else 350
        return COL_INFRA, infra_y
        
    # Default fallback
    return 50, 50

# Defining relationships as source -> target lists for lines
def get_relationships() -> list[Tuple[str, str, bool]]:
    # source_node_substring, target_node_substring, is_confirmed (solid vs dashed)
    return [
        # Nemoclaw dispatch contracts
        ("nemoclaw", "qwen", True),
        ("nemoclaw", "glm", False), # GLM has gap
        ("nemoclaw", "evaluator", False),
        
        # Nemotron classifications to dispatch
        ("nemotron", "nemoclaw", False), # Nemotron gap
        
        # Tools
        ("qwen", "mcp-context7", True),
        ("qwen", "mcp-server-filesystem", True),
        ("qwen", "mcp-playwright", True),
        ("evaluator", "mcp-server-sequential-thinking", True),
        ("openclaw", "mcp-server-filesystem", False)
    ]
