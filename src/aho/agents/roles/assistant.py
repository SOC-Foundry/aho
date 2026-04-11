"""Assistant — general-purpose helper role."""
from aho.agents.roles.base_role import AgentRole


ASSISTANT_ROLE = AgentRole(
    name="assistant",
    system_prompt="You are a helpful assistant. Answer concisely. If asked to do something you cannot do, say so plainly.",
    allowed_tools=["chat"],
)
