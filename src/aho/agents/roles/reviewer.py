"""Reviewer — role for reviewing aho artifacts (full implementation deferred to 0.1.8)."""
from aho.agents.roles.base_role import AgentRole


REVIEWER_ROLE = AgentRole(
    name="reviewer",
    system_prompt="You are an artifact reviewer. Read the provided content and identify concerns. Do not modify the content.",
    allowed_tools=["chat"],
)
