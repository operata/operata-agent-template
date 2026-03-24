"""Project configuration — the values you change to make this agent yours.

This file centralizes settings that a developer needs to customize.
Everything reads from environment variables with sensible defaults.

TODO: Update these defaults for your org and use case.
"""

import os

# ---------------------------------------------------------------------------
# Organization defaults
# ---------------------------------------------------------------------------

# TODO: Set your Jira instance URL
JIRA_BASE_URL = os.environ.get("JIRA_URL", "https://your-org.atlassian.net")

# TODO: Set your GitHub org name
GITHUB_ORG = os.environ.get("GITHUB_ORG", "your-org")

# TODO: Set your Buildkite org slug (if using Buildkite)
BUILDKITE_ORG = os.environ.get("BUILDKITE_ORG", "your-org")

# ---------------------------------------------------------------------------
# Jira project identifiers — used for auto-linking tickets in Slack
# ---------------------------------------------------------------------------

# TODO: Replace with your Jira project key prefixes
JIRA_TICKET_PREFIXES = ["PROJ"]

# ---------------------------------------------------------------------------
# Slack channel name → env var mapping
# The bot must be a member of each channel.
# ---------------------------------------------------------------------------

# TODO: Replace with the channels your agent reads/writes
SLACK_CHANNEL_ENV_MAP = {
    # "my-channel": "SLACK_CHANNEL_MY_CHANNEL",
}

# ---------------------------------------------------------------------------
# AWS / Bedrock
# ---------------------------------------------------------------------------

AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-6-v1")
