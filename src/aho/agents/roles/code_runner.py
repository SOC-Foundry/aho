"""Code runner — role for code execution tasks."""
from aho.agents.roles.base_role import AgentRole


CODE_RUNNER_ROLE = AgentRole(
    name="code_runner",
    system_prompt="You are a code runner. When asked to solve a problem, write minimal code and execute it. Report the result factually.",
    allowed_tools=["chat", "execute_code"],
)
