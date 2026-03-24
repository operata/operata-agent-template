"""MCP client factories for external service integrations.

Each factory returns an MCPClient that can be passed directly to
Agent(tools=[...]) — Strands manages the connection lifecycle automatically.

TODO: Uncomment and configure the factories you need. Delete the rest.

Usage:
    from tools.mcp_tools import create_jira_mcp

    jira = create_jira_mcp(dry_run=True)
    agent = Agent(tools=[jira, *other_tools])
"""

import logging
import os
import sys

from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Jira via mcp-atlassian (https://github.com/sooperset/mcp-atlassian)
# ---------------------------------------------------------------------------

_JIRA_READ_TOOLS = [
    "jira_search",
    "jira_get_issue",
    "jira_get_project_issues",
    "jira_get_board_issues",
    "jira_get_sprint_issues",
    "jira_get_sprints_from_board",
    "jira_get_agile_boards",
    "jira_get_transitions",
    "jira_get_all_projects",
    "jira_batch_get_changelogs",
    "jira_get_worklog",
    "jira_search_fields",
    "jira_get_issue_development_info",
]

_JIRA_WRITE_TOOLS = [
    "jira_add_comment",
    "jira_transition_issue",
    "jira_update_issue",
]


def create_jira_mcp(dry_run: bool = True) -> MCPClient:
    """Create an MCP client for Jira via mcp-atlassian.

    Requires env vars: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
    """
    allowed = list(_JIRA_READ_TOOLS)
    if not dry_run:
        allowed.extend(_JIRA_WRITE_TOOLS)

    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=["-c", "from mcp_atlassian import main; main()"],
                env={
                    "JIRA_URL": os.environ.get("JIRA_URL", ""),
                    "JIRA_USERNAME": os.environ.get("JIRA_EMAIL", ""),
                    "JIRA_API_TOKEN": os.environ.get("JIRA_API_TOKEN", ""),
                    "TOOLSETS": "jira_issues,jira_fields,jira_transitions,jira_agile,jira_worklog,jira_development",
                    "CONFLUENCE_URL": "",
                    "CONFLUENCE_USERNAME": "",
                    "CONFLUENCE_API_TOKEN": "",
                },
            )
        ),
        tool_filters={"allowed": allowed},
    )


# ---------------------------------------------------------------------------
# Example: GitHub MCP (Docker-based, local dev only)
# ---------------------------------------------------------------------------
#
# import re
#
# _GITHUB_ALLOWED_TOOLS = [
#     re.compile(r"^list_pull_requests$"),
#     re.compile(r"^get_pull_request$"),
#     re.compile(r"^list_commits$"),
#     re.compile(r"^list_workflow_runs$"),
# ]
#
# def create_github_mcp() -> MCPClient | None:
#     token = os.environ.get("GITHUB_TOKEN", "")
#     if not token:
#         return None
#     return MCPClient(
#         lambda: stdio_client(StdioServerParameters(
#             command="docker",
#             args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
#                   "ghcr.io/github/github-mcp-server"],
#             env={"GITHUB_PERSONAL_ACCESS_TOKEN": token},
#         )),
#         tool_filters={"allowed": _GITHUB_ALLOWED_TOOLS},
#     )
