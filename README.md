# Agent Template

A template for building autonomous agents with [Strands Agents SDK](https://github.com/strands-agents/strands-agents) and [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/).

## What you get

- Agent runner with dry-run/live modes and output saving
- AgentCore Runtime entry point for cloud deployment
- Slack integration with Block Kit, auto-linking, and @mentions
- AgentCore Memory for cross-run persistence
- MCP client factory patterns (Jira example included)
- Environment validation script
- Claude Code slash commands (`/run`, `/deploy`, `/logs`, `/status`)
- EventBridge Lambda trigger for scheduled runs
- Tests, linting, and Makefile workflow

## Quick start

```bash
# Clone the template
git clone https://github.com/johnoperata/operata-agent-template.git my-agent
cd my-agent
rm -rf .git && git init

# Set up
make setup              # Creates venv, installs deps, copies .env

# Customize (in order of importance)
# 1. Edit prompts/agent.md — the system prompt (80% of the work)
# 2. Edit config.py — org settings, Slack channels, Jira prefixes
# 3. Edit agent_config.py — enable your data source tools
# 4. Edit agent.py — the prompt that drives each run
# 5. Fill in .env with your tokens

# Run
make run                # Dry-run (no external writes)
make run-live           # Full run (posts to Slack)

# Deploy
agentcore configure -e agent_runtime.py -n my-agent -rt PYTHON_3_12 -r us-west-2
agentcore deploy
```

## Architecture

```
EventBridge cron / manual trigger
  → AgentCore Runtime (agent_runtime.py)
    → Bedrock Claude (inference)
    → AgentCore Memory (read/write findings)
    → Your data sources (Jira, GitHub, etc.)
    → Slack (post output)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add tools, data sources, and agent modes.

## Reference implementation

The [delivery-lead-agent](https://github.com/johnoperata/operata-delivery-lead-agent) is a production agent built from this template. Use it as a quality reference for system prompts, tool implementations, and deployment patterns.
