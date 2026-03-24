Deploy the agent to AWS Bedrock AgentCore.

Arguments: $ARGUMENTS

## Steps

### 1. Check AWS credentials
Run `aws sts get-caller-identity` first. If this fails, stop and tell the user to set `AWS_PROFILE` or refresh credentials.

### 2. Check git status
Run `git status --short` and `git log --oneline -1`.

- If there are uncommitted changes: show what's dirty, then commit and push. Use the standard git commit flow — stage files, draft a message, commit, push.
- If clean but local is ahead of remote: push.
- If clean and up to date: skip to deploy.

### 3. Deploy to AgentCore
Run (with 5 minute timeout):
```
source .venv/bin/activate && agentcore deploy 2>&1
```

This uploads the code package to S3 and deploys to the AgentCore runtime. Takes 1-3 minutes. The command reads `.bedrock_agentcore.yaml` for all config automatically.

If the user passed arguments like `--env KEY=VALUE`, append them to the deploy command.

### 4. Verify
Run:
```
source .venv/bin/activate && agentcore status 2>&1
```

Confirm the endpoint shows "Ready". Extract and display:
- Agent name and ARN
- Endpoint status
- Last updated timestamp

### 5. Report
Print a clear summary:
- What was committed (if anything)
- Deploy result (success/failure)
- Endpoint status
- How to invoke: `agentcore invoke '{"mode": "default", "dry_run": true}'`

## Error handling
- AWS credential failure: tell user to run `export AWS_PROFILE=<profile>` or check SSO
- Deploy failure: show the error output, suggest checking CloudWatch logs
- Timeout: the deploy command can take up to 3 minutes, use timeout of 300000ms
