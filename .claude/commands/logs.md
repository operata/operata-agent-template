View AgentCore runtime logs for the agent.

Arguments: $ARGUMENTS

## Mode dispatch

| Arguments | What it does |
|-----------|-------------|
| empty or `tail` | Tail the most recent CloudWatch logs (last 30 minutes) |
| `errors` | Show only error-level log entries from the last 24 hours |
| `last` | Show logs from the last invocation only |
| `1h` / `2h` / `6h` / `24h` | Tail logs for the specified time window |

## Step 1: Read config

Read `.bedrock_agentcore.yaml` to get the agent ID and log group. The log group follows the pattern:
```
/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT
```

Extract the `agent_id` from the YAML file under `agents.<agent_name>.bedrock_agentcore.agent_id`.

## Step 2: Fetch logs

### Mode: `tail` (default)
```
aws logs tail "/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT" \
  --log-stream-name-prefix "$(date -u +%Y/%m/%d)/[runtime-logs" \
  --since 30m \
  --format short 2>&1
```

### Mode: `errors`
```
aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT" \
  --start-time $(python3 -c "import time; print(int((time.time() - 86400) * 1000))") \
  --filter-pattern "ERROR" \
  --output text 2>&1
```

### Mode: `last`
First get the most recent log stream:
```
aws logs describe-log-streams \
  --log-group-name "/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT" \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --output json 2>&1
```
Then tail that specific stream.

### Mode: time window (e.g. `2h`)
Parse the number and unit. Use `--since <value>` with `aws logs tail`.

## Step 3: Present the output

Filter and format the logs for readability:
- **Strip noise:** Remove httpx INFO lines, botocore credential lines
- **Highlight errors:** Any line containing ERROR, Exception, Traceback
- **Show tool calls:** Lines showing tool invocations

Present a summary at the top:
- Time range covered
- Total log lines (before filtering)
- Error count

## Error handling
- If no logs found: the agent may not have run recently
- If access denied: check AWS credentials and region
