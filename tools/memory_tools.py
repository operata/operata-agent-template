"""AgentCore Memory tools.

Provides both:
1. Session management (auto-extraction from conversation via AgentCoreMemorySessionManager)
2. Explicit memory operations (@tool functions for record, retrieve, list)

Environment variables:
    AGENTCORE_MEMORY_ID — Memory resource ID (created by get_or_create_memory)
    AWS_REGION — AWS region (default: us-west-2)
"""

import json
import logging
import os
from datetime import datetime, timezone

import boto3
from botocore.config import Config as BotocoreConfig
from strands import tool

from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

logger = logging.getLogger(__name__)

# TODO: Update these to match your agent
ACTOR_ID = "my-agent"
DEFAULT_NAMESPACE = "/my-agent/"


def _memory_client():
    """Get a boto3 client for the AgentCore Memory service."""
    config = BotocoreConfig(user_agent_extra=ACTOR_ID)
    return boto3.client(
        "bedrock-agentcore",
        region_name=os.environ.get("AWS_REGION", "us-west-2"),
        config=config,
    )


def _memory_id():
    return os.environ.get("AGENTCORE_MEMORY_ID", "")


# ---------------------------------------------------------------------------
# Session management (auto-extraction from conversation)
# ---------------------------------------------------------------------------


def get_or_create_memory() -> str:
    """Create the AgentCore Memory resource if it doesn't exist.

    Run this once during initial setup. The memory_id is then stored
    in .env for subsequent runs.
    """
    client = MemoryClient(region_name=os.environ.get("AWS_REGION", "us-west-2"))
    # TODO: Update the memory name, description, and namespace templates
    memory = client.create_memory_and_wait(
        name="AgentMemory",
        description="Agent memory — tracks findings across runs",
        strategies=[
            {
                "semanticMemoryStrategy": {
                    "name": "SemanticTracker",
                    "namespaceTemplates": [f"/{ACTOR_ID}/{{actorId}}/semantic/"],
                }
            },
            {
                "summaryMemoryStrategy": {
                    "name": "RunSummaries",
                    "namespaceTemplates": [f"/{ACTOR_ID}/{{actorId}}/summaries/{{sessionId}}/"],
                }
            },
        ],
    )
    memory_id = memory.get("id")
    logger.info("Created AgentCore Memory: %s", memory_id)
    print(f"Created AgentCore Memory: {memory_id}")
    print(f"Add to .env: AGENTCORE_MEMORY_ID={memory_id}")
    return memory_id


def create_memory_session(session_id: str) -> AgentCoreMemorySessionManager | None:
    """Create a memory session manager for a Strands agent run.

    Each run gets its own session_id (e.g. 'run-2026-04-07').
    The actor_id is constant so long-term memories accumulate across all sessions.
    """
    mid = _memory_id()
    if not mid:
        logger.warning("AGENTCORE_MEMORY_ID not set. Running without memory.")
        return None

    config = AgentCoreMemoryConfig(
        memory_id=mid,
        session_id=session_id,
        actor_id=ACTOR_ID,
    )
    return AgentCoreMemorySessionManager(config, region_name=os.environ.get("AWS_REGION", "us-west-2"))


# ---------------------------------------------------------------------------
# Explicit memory tools (@tool functions)
# ---------------------------------------------------------------------------


@tool
def record_memory(content: str) -> str:
    """Record an observation to AgentCore long-term memory.

    Use this to persist important findings that should carry over to future runs.
    Content is semantically indexed and retrievable via retrieve_memories.
    """
    mid = _memory_id()
    if not mid:
        return json.dumps({"recorded": False, "error": "AGENTCORE_MEMORY_ID not set"})

    client = _memory_client()
    session_id = f"memory-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    try:
        client.create_event(
            memoryId=mid,
            actorId=ACTOR_ID,
            sessionId=session_id,
            eventTimestamp=datetime.now(timezone.utc),
            payload=[
                {
                    "conversational": {
                        "content": {"text": content},
                        "role": "ASSISTANT",
                    }
                }
            ],
        )
        logger.info("Recorded memory: %s", content[:100])
        return json.dumps({"recorded": True, "content_preview": content[:200]})
    except Exception as e:
        logger.error("Failed to record memory: %s", e)
        return json.dumps({"recorded": False, "error": str(e)})


@tool
def retrieve_memories(query: str, max_results: int = 10) -> str:
    """Search long-term memory using semantic similarity.

    Use this at the start of every run to recall findings from previous runs.
    Returns memories ranked by relevance with content, score, and creation date.
    """
    mid = _memory_id()
    if not mid:
        return json.dumps({"error": "AGENTCORE_MEMORY_ID not set"})

    client = _memory_client()
    try:
        response = client.retrieve_memory_records(
            memoryId=mid,
            namespace=DEFAULT_NAMESPACE,
            searchCriteria={
                "searchQuery": query,
                "topK": max_results,
            },
        )
        records = []
        for record in response.get("memoryRecordSummaries", []):
            created = record.get("createdAt", "")
            records.append(
                {
                    "id": record.get("memoryRecordId", ""),
                    "content": record.get("content", {}).get("text", ""),
                    "score": record.get("score", 0),
                    "created": created.isoformat() if hasattr(created, "isoformat") else str(created),
                    "namespace": record.get("namespace", ""),
                }
            )
        return json.dumps({"query": query, "count": len(records), "records": records}, indent=2)
    except Exception as e:
        logger.error("Failed to retrieve memories: %s", e)
        return json.dumps({"error": str(e)})


@tool
def list_memories(max_results: int = 20) -> str:
    """List recent memories from AgentCore long-term memory.

    Useful for reviewing what has been stored across previous runs.
    """
    mid = _memory_id()
    if not mid:
        return json.dumps({"error": "AGENTCORE_MEMORY_ID not set"})

    client = _memory_client()
    try:
        response = client.list_memory_records(
            memoryId=mid,
            namespace=DEFAULT_NAMESPACE,
            maxResults=max_results,
        )
        records = []
        for record in response.get("memoryRecordSummaries", []):
            created = record.get("createdAt", "")
            records.append(
                {
                    "id": record.get("memoryRecordId", ""),
                    "content_preview": record.get("content", {}).get("text", "")[:300],
                    "created": created.isoformat() if hasattr(created, "isoformat") else str(created),
                    "namespace": record.get("namespace", ""),
                }
            )
        return json.dumps({"count": len(records), "records": records}, indent=2)
    except Exception as e:
        logger.error("Failed to list memories: %s", e)
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Exported tools list
# ---------------------------------------------------------------------------

MEMORY_TOOLS = [record_memory, retrieve_memories, list_memories]


if __name__ == "__main__":
    get_or_create_memory()
