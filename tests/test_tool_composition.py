"""Tests for tool exports and composition — no credentials needed."""


def test_slack_tools_export():
    """Verify Slack tool lists are populated."""
    from tools import SLACK_READ_TOOLS, SLACK_TOOLS, SLACK_WRITE_TOOLS

    assert len(SLACK_READ_TOOLS) > 0
    assert len(SLACK_WRITE_TOOLS) > 0
    assert len(SLACK_TOOLS) == len(SLACK_READ_TOOLS) + len(SLACK_WRITE_TOOLS)


def test_memory_tools_export():
    """Verify memory tool list is populated."""
    from tools import MEMORY_TOOLS

    assert len(MEMORY_TOOLS) > 0


def test_system_prompt_loadable():
    """Verify the system prompt file exists and is non-empty."""
    from pathlib import Path

    prompt_path = Path(__file__).parent.parent / "prompts" / "agent.md"
    assert prompt_path.exists(), f"System prompt not found at {prompt_path}"
    content = prompt_path.read_text()
    assert len(content) > 100, "System prompt seems too short"


def test_config_importable():
    """Verify config.py has expected attributes."""
    import config

    assert hasattr(config, "JIRA_BASE_URL")
    assert hasattr(config, "SLACK_CHANNEL_ENV_MAP")
    assert hasattr(config, "MODEL_ID")
    assert hasattr(config, "AWS_REGION")
