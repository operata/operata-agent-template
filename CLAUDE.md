# Agent Template

## What this is

A template for building autonomous agents with Strands Agents SDK, deployed to AWS Bedrock AgentCore. Clone this, customize it for your use case, and deploy.

This is the scaffolding — the delivery-lead-agent is the reference implementation.

## Tech stack

- **Runtime:** Strands Agents SDK (Python)
- **Inference:** AWS Bedrock (Claude Sonnet 4.6 by default, configurable in config.py)
- **Hosting:** AWS Bedrock AgentCore Runtime
- **Memory:** AWS Bedrock AgentCore Memory (semantic + summary strategies)
- **Integrations:** Slack (Block Kit), Jira (MCP), and extensible via @tool or MCP
- **Deployment:** AgentCore Starter Toolkit CLI

## Project structure

```
agent-template/
├── CLAUDE.md                     # You are here
├── README.md                     # Project overview and quick start
├── CONTRIBUTING.md               # How to add tools, modes, and data sources
├── Makefile                      # make setup / run / test / deploy
├── config.py                     # Org-specific settings (TODO markers)
├── agent_config.py               # Model, prompt, tool composition
├── agent.py                      # Primary agent mode
├── agent_runtime.py              # AgentCore entry point
├── .env.example                  # Template for env vars
├── pyproject.toml                # Dependencies
├── requirements.txt              # Runtime deps
├── slack_users.json              # Team name → Slack UID map (empty)
├── prompts/
│   └── agent.md                  # System prompt (TODO — the soul of the agent)
├── tools/
│   ├── __init__.py               # Tool exports
│   ├── mcp_tools.py              # MCP client factories (Jira example, commented)
│   ├── slack_tools.py            # Slack Block Kit formatting, @mentions, auto-linking
│   └── memory_tools.py           # AgentCore Memory (record, retrieve, list)
├── scripts/
│   └── check_env.py              # Environment validation (make check)
├── tests/
│   ├── __init__.py
│   └── test_tool_composition.py  # Tool wiring tests
├── .claude/
│   └── commands/                 # Claude Code slash commands
│       ├── run.md                # /run — dry, live modes
│       ├── deploy.md             # /deploy — commit, push, deploy
│       ├── logs.md               # /logs — CloudWatch log inspection
│       └── status.md             # /status — system dashboard
├── lambda/
│   └── trigger.py                # EventBridge → AgentCore Lambda wrapper
└── docs/
    └── ARCHITECTURE.md           # System design template
```

## Customization points

Files with `TODO` markers that need your input:

| File | What to change |
|------|---------------|
| `prompts/agent.md` | **System prompt — 80% of customization.** Define the agent's role, data sources, output format. |
| `config.py` | Org name, Jira URL, ticket prefixes, Slack channels |
| `agent_config.py` | Tool composition — enable/disable data sources |
| `agent.py` | Primary mode prompt — what to query and how to format |
| `slack_users.json` | Team name → Slack UID mapping |
| `.env` | API tokens, channel IDs, memory ID |

## How tools work

Two types, composed in `agent_config.py:build_tools()`:

1. **MCP clients** (`tools/mcp_tools.py`) — external services via Model Context Protocol. Jira factory included as example.
2. **@tool functions** — custom implementations. Slack (Block Kit) and Memory included. Add your own in `tools/`.

DRY_RUN gating: Write tools are excluded at composition time in `build_tools()`.

## Developer workflow

```
/run dry                    # Local dry-run (~3 min)
/run live                   # Deploy + invoke
/deploy                     # Commit, push, deploy to AgentCore
/logs                       # Tail recent CloudWatch logs
/status                     # Full system dashboard
```

## How to run locally

```bash
make setup                  # First time: venv + deps + env check
make run                    # Dry-run
make run-live               # Full run (writes to Slack)
make test                   # Unit tests
make lint                   # Check code style
```

## How to deploy

```bash
# First time: configure the runtime
agentcore configure -e agent_runtime.py -n my-agent \
  -rt PYTHON_3_12 -r us-west-2 \
  --idle-timeout 900 --max-lifetime 3600

# Deploy
agentcore deploy

# Test
agentcore invoke '{"mode": "default", "dry_run": true}'
```

## Conventions

- MCP client factories live in `tools/mcp_tools.py`
- @tool functions live in their respective `tools/*.py` files
- System prompt is a standalone file in `prompts/` — iterated independently of code
- All secrets from environment variables, never hardcoded
- Architecture decisions go in `docs/` with date, context, and rationale
- Format with `ruff format`, lint with `ruff check`
