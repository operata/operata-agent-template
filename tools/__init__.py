"""Agent Tools

Tools come from two sources:

1. MCP clients — external services via Model Context Protocol
   Created via factory functions in tools/mcp_tools.py.

2. @tool functions — custom implementations for Slack, Memory, etc.

Usage in agent.py:

    from tools.memory_tools import MEMORY_TOOLS, create_memory_session
    from tools.slack_tools import post_to_slack, read_slack_thread

    tools = [*MEMORY_TOOLS, post_to_slack, read_slack_thread]
    agent = Agent(tools=tools)
"""

# @tool functions — Slack
from tools.slack_tools import (
    post_to_slack,
    read_channel_history,
    read_slack_thread,
)

# @tool functions — Memory
from tools.memory_tools import MEMORY_TOOLS, create_memory_session

# Convenience lists
SLACK_READ_TOOLS = [read_slack_thread, read_channel_history]
SLACK_WRITE_TOOLS = [post_to_slack]
SLACK_TOOLS = SLACK_READ_TOOLS + SLACK_WRITE_TOOLS

__all__ = [
    # Slack @tools
    "SLACK_TOOLS",
    "SLACK_READ_TOOLS",
    "SLACK_WRITE_TOOLS",
    # Memory
    "MEMORY_TOOLS",
    "create_memory_session",
]
