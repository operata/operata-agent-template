Run the agent in the specified mode.

Arguments: $ARGUMENTS

## Mode dispatch

Parse the arguments to determine mode:

| Arguments | Mode | What happens |
|-----------|------|-------------|
| `dry` or empty | Local dry run | Runs `python agent.py --dry-run` locally. No external writes. |
| `live` | Full production run | Deploys to AgentCore, then invokes remotely. Posts to Slack. |

## Mode: `dry` (default)

### 1. Check credentials
Run `aws sts get-caller-identity` — the agent needs live AWS access even locally (Bedrock, Memory).

### 2. Run the agent
Run with a **10 minute timeout** (agent runs take 2-8 minutes):
```
source .venv/bin/activate && python agent.py --dry-run 2>&1
```
Use `timeout: 600000` on the Bash call.

### 3. Present the output
Scan the output for:
- The output text (look for section headers)
- Any tool call errors (look for "Error calling tool" or "HTTPError")
- The final "Run completed" line

Present a summary:
- **Tool calls:** count of successful vs failed
- **Errors:** any API failures or MCP connection issues
- **Output preview:** show the first ~50 lines of actual output (not log lines)

## Mode: `live`

### 1. Deploy first
Follow the full `/deploy` workflow: check git, commit if dirty, push, deploy to AgentCore, verify endpoint.

### 2. Invoke on AgentCore
Run with a **10 minute timeout**:
```
source .venv/bin/activate && agentcore invoke '{"mode": "default"}' 2>&1
```

### 3. Verify
After invoke completes, check that the output was posted correctly.

Report: deploy status, invoke result, and whether the output landed in Slack.

## Error handling
- If the agent crashes with a Python exception, show the traceback and suggest checking `.env` for missing tokens
- If MCP client fails to initialize, suggest checking the MCP package installation
- If Bedrock throttling occurs, wait 30 seconds and suggest retrying
- Always show how long the run took
