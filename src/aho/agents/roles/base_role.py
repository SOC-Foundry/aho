"""Base role definition for OpenClaw agents."""
from dataclasses import dataclass, field


@dataclass
class AgentRole:
    name: str
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=lambda: ["chat"])
