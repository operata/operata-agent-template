"""Shared agent configuration — model, prompt, and tool composition.

Both agent.py (primary mode) and any additional modes import from here.
This avoids duplicating model setup and tool wiring.

To customize the agent:
- Change the model: update MODEL_ID in config.py or set MODEL_ID env var
- Change the prompt: edit prompts/<agent_name>.md
- Change the tools: modify build_tools() below
"""

import os
from pathlib import Path

from strands.models.bedrock import BedrockModel

from config import AWS_REGION, MODEL_ID
from tools.memory_tools import MEMORY_TOOLS
from tools.slack_tools import (
    post_to_slack,
    read_channel_history,
    read_slack_thread,
)

# TODO: Update the prompt filename to match your agent
SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "agent.md").read_text()

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

MODEL = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION)


def build_tools(dry_run: bool = False, mode: str = "default") -> list:
    """Compose MCP clients + @tool functions for an agent run.

    Args:
        dry_run: If True, exclude write tools.
        mode: Agent mode — extend for additional modes.
    """
    tools: list = []

    # -- @tool: Memory (record, retrieve, list) --
    tools.extend(MEMORY_TOOLS)

    # -- @tool: Slack read (always available) --
    tools.extend([read_slack_thread, read_channel_history])

    # -- @tool: Slack write (when not dry-run) --
    if not dry_run:
        tools.append(post_to_slack)

    # TODO: Add your data source tools here. Examples:
    #
    # -- MCP: Jira --
    # from tools.mcp_tools import create_jira_mcp
    # tools.append(create_jira_mcp(dry_run=dry_run))
    #
    # -- @tool: GitHub REST API (optional, needs GITHUB_TOKEN) --
    # from tools.github_tools import GITHUB_TOOLS
    # if os.environ.get("GITHUB_TOKEN"):
    #     tools.extend(GITHUB_TOOLS)

    return tools
