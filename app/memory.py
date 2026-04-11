from uuid import uuid4

from vanna.core.tool import ToolContext
from vanna.core.user.models import User
from vanna.integrations.local.agent_memory import DemoAgentMemory


def create_agent_memory(max_items: int = 1000) -> DemoAgentMemory:
    return DemoAgentMemory(max_items=max_items)


def build_tool_context(agent_memory: DemoAgentMemory) -> ToolContext:
    return ToolContext(
        user=User(
            id="default_user",
            email="user@example.com",
            group_memberships=[],
        ),
        conversation_id="nl2sql-api",
        request_id=str(uuid4()),
        agent_memory=agent_memory,
    )


def count_memories(agent_memory: DemoAgentMemory) -> int:
    return len(agent_memory._memories)

