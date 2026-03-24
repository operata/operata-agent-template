# Architecture

## Overview

An autonomous agent that runs on AgentCore, producing structured output and posting to Slack.

## Data flow

```
SCHEDULED (cron or manual)
  EventBridge cron / manual trigger
    → AgentCore Runtime (agent.py)
      → Bedrock Claude (inference)
      → AgentCore Memory (read previous findings, write today's)
      → Your data sources (Jira, GitHub, etc.)
      → Slack API (post output)
```

## Memory model

AgentCore Memory with two extraction strategies:

- **SemanticTracker:** Extracts key signals for semantic search across runs.
- **RunSummaries:** Summarises each run for quick cross-day reference.

Actor ID is constant. Session ID is date-based. Long-term memories accumulate under the actor.

## Security

- API tokens in Secrets Manager, injected via AgentCore config
- Bedrock access via IAM task role on AgentCore Runtime
- DRY_RUN gating removes write tools at composition time

## Cost estimate

- Claude Sonnet 4.6 inference: ~$0.50-2 per run
- AgentCore Runtime: seconds of compute per run, negligible
- AgentCore Memory: per-event pricing, negligible at 1 run/day
