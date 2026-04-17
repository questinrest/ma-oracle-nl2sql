from uuid import uuid4

from vanna.capabilities.agent_memory import AgentMemory
from vanna.core.tool import ToolContext
from vanna.core.user.models import User
from vanna.integrations.chromadb.agent_memory import ChromaAgentMemory
from vanna.integrations.pinecone.agent_memory import PineconeAgentMemory
from vanna.integrations.local.agent_memory import DemoAgentMemory

from app.config import Settings


def create_agent_memory(settings: Settings, max_items: int = 1000) -> AgentMemory:
    if settings.memory_type == "chroma":
        return ChromaAgentMemory(
            persist_directory=settings.chroma_path,
            collection_name="nl2sql_memory",
        )
    elif settings.memory_type == "pinecone":
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be set when memory_type is pinecone")
        return PineconeAgentMemory(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
            environment=settings.pinecone_environment,
            dimension=settings.pinecone_dimension,
            metric=settings.pinecone_metric,
        )
    return DemoAgentMemory(max_items=max_items)


def build_tool_context(agent_memory: AgentMemory) -> ToolContext:
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


def count_memories(agent_memory: AgentMemory) -> int:
    if isinstance(agent_memory, DemoAgentMemory):
        return len(agent_memory._memories)
    try:
        if hasattr(agent_memory, "_get_collection"):
            return agent_memory._get_collection().count()
        elif hasattr(agent_memory, "_get_index"):
            stats = agent_memory._get_index().describe_index_stats()
            return stats.get("total_vector_count", 0)
    except Exception:
        pass
    return 0

