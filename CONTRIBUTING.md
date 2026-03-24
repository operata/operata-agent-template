# Build Your Own Agent

This template is designed to be customized. The architecture supports any domain — customer success, incident response, sales pipeline, security audit, whatever needs autonomous intelligence.

## Quick orientation

The agent has three layers:

1. **System prompt** (`prompts/agent.md`) — defines *who* the agent is, *what* it knows, and *how* it behaves. This is where 80% of customization happens.
2. **Tools** (`tools/*.py`) — define *what the agent can do*: read data, post to Slack, remember things.
3. **Agent runner** (`agent.py`) — wires it all together and runs it. Thin file, rarely changed.

Configuration lives in `config.py` (org-specific defaults) and `.env` (secrets).

## Adding a new tool

Tools are Python functions decorated with `@tool` from Strands:

### Step 1: Create the tool file

```python
# tools/my_tool.py
import json
import requests
from strands import tool

@tool
def get_incidents(status: str = "open", max_results: int = 10) -> str:
    """Get incidents from the incident management system.

    Args:
        status: Filter by status ('open', 'resolved', 'all')
        max_results: Maximum incidents to return
    """
    resp = requests.get("https://api.example.com/incidents", ...)
    return json.dumps({"incidents": resp.json()})

MY_TOOLS = [get_incidents]
```

### Step 2: Register in agent_config.py

```python
from tools.my_tool import MY_TOOLS

def build_tools(dry_run=False, mode="default"):
    tools = [...]
    tools.extend(MY_TOOLS)
    return tools
```

### Step 3: Tell the prompt about it

Add a section to your system prompt explaining when and how to use it.

## Adding an MCP data source

For services with an MCP server, use MCP instead of `@tool`:

```python
# tools/mcp_tools.py — add a new factory

def create_my_mcp() -> MCPClient | None:
    token = os.environ.get("MY_SERVICE_TOKEN", "")
    if not token:
        return None

    return MCPClient(
        lambda: stdio_client(StdioServerParameters(
            command="uvx",
            args=["my-mcp-server"],
            env={"API_TOKEN": token},
        )),
    )
```

Then add to `build_tools()`:

```python
my_mcp = create_my_mcp()
if my_mcp:
    tools.append(my_mcp)
```

MCP is preferred when a community-maintained server exists. Use `@tool` when you need custom formatting or business logic.

## Adding a new agent mode

### 1. Create the runner

```python
# agent_weekly.py
from agent_config import MODEL, SYSTEM_PROMPT, build_tools
from tools.memory_tools import create_memory_session

def run_weekly():
    agent = Agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=build_tools(dry_run=False, mode="weekly"),
        session_manager=create_memory_session(session_id="weekly-2026-W13"),
    )
    result = agent("Generate the weekly review...")
    return result
```

### 2. Add dispatch in agent_runtime.py

```python
elif mode == "weekly":
    from agent_weekly import run_weekly
    result = run_weekly()
```

### 3. Add a Makefile target

```makefile
weekly: ## Run weekly review
	$(ACTIVATE) && $(PYTHON) agent_weekly.py
```

## Deploying to AgentCore

```bash
# First time: configure the runtime
agentcore configure -e agent_runtime.py -n my-agent \
  -rt PYTHON_3_12 -r us-west-2 \
  --idle-timeout 900 --max-lifetime 3600

# Deploy
agentcore deploy

# Test
agentcore invoke '{"mode": "default", "dry_run": true}'

# Set up daily schedule (EventBridge cron)
# See lambda/trigger.py for the Lambda wrapper
```

## Iterating on the prompt

The prompt is the soul of the agent. The iteration cycle:

1. Edit `prompts/agent.md`
2. `make run` (dry-run, ~3 minutes)
3. Read the output — is it what you'd want to see?
4. Repeat

Tips:
- Be specific. "Check Jira" is worse than "Search Jira for tickets with status 'In Progress' that haven't been updated in 3+ days."
- Add examples of good output in the prompt.
- Set explicit limits: "Maximum 3 questions per run."
- Use the "Never do" section liberally.
- Test with `--dry-run` before deploying live.

## Code style

- Format with `ruff format`, lint with `ruff check`
- Run `make lint` before committing
- Tests run with `make test` — add tests for any pure logic
