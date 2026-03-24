Show the full status of the agent system — runtime, deployment, recent activity, and git state.

Arguments: $ARGUMENTS

## Gather data

Run these commands in parallel where possible, then synthesise into a single status report.

### 1. AgentCore runtime status
```
source .venv/bin/activate && agentcore status 2>&1
```
Extract: agent state (Ready/Not Ready), endpoint status, agent ARN, last updated timestamp.

### 2. Git state
Run in parallel:
```
git log --oneline -5
```
```
git status --short
```
```
git rev-parse --abbrev-ref HEAD
```
Extract: current branch, latest commit, whether there are uncommitted changes.

### 3. Recent errors (last 3 days)
Read `.bedrock_agentcore.yaml` to get the agent ID, then:
```
aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT" \
  --start-time $(python3 -c "import time; print(int((time.time() - 259200) * 1000))") \
  --filter-pattern "ERROR" \
  --max-items 10 \
  --output json 2>&1
```
Count errors. If access fails, just note "unable to check logs."

## Present the status report

Format as a clean, scannable summary:

```
## Agent — System Status

**Runtime**
  State:        Ready / Not Ready
  Agent:        <agent-name>
  ARN:          arn:aws:bedrock-agentcore:...
  Last deploy:  <timestamp>

**Git**
  Branch:   main @ <sha>
  Status:   clean / N files modified
  Ahead:    up to date / N commits ahead of origin

**Recent activity**
  Errors (3d):  N errors found / no errors
  Last 5 commits:
    <commit log>

**Quick commands**
  /run dry              Local dry-run
  /run live             Deploy + invoke
  /deploy               Deploy without invoking
  /logs                 Tail recent logs
  /logs errors          Show errors only
```

## Error handling
- If `agentcore status` fails, the agent may not be configured. Suggest running `agentcore deploy` first.
- If AWS credentials are expired, note this prominently at the top of the report.
