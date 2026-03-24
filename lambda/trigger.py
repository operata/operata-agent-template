"""EventBridge → AgentCore Runtime trigger Lambda.

Receives EventBridge events (cron schedule or custom rules) and invokes
the agent on AgentCore Runtime.

Environment variables:
    AGENT_RUNTIME_ARN — AgentCore Runtime ARN
    AWS_REGION — AWS region (default: us-west-2)

EventBridge input format:
    {
        "detail": {
            "mode": "default"
        }
    }

Lambda config: Python 3.12, 256 MB, 600s timeout.
"""

import json
import os
import uuid

import boto3

AGENT_ARN = os.environ["AGENT_RUNTIME_ARN"]
REGION = os.environ.get("AWS_REGION", "us-west-2")


def handler(event, context):
    """Handle EventBridge event and invoke AgentCore Runtime."""
    client = boto3.client("bedrock-agentcore", region_name=REGION)

    detail = event.get("detail", {})
    mode = detail.get("mode", "default")

    payload = {"mode": mode}

    # TODO: Add additional payload fields for your modes. Example:
    # if mode == "triage":
    #     payload["ticket_key"] = detail.get("ticket_key", "")

    session_id = f"{mode}-{uuid.uuid4()}"

    print(f"Invoking agent: mode={mode}, session={session_id}")

    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps(payload).encode(),
        contentType="application/json",
        accept="application/json",
    )

    content = []
    for chunk in response.get("response", []):
        content.append(chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk))

    print(f"Agent completed: mode={mode}, session={session_id}")
    return {
        "statusCode": 200,
        "body": json.dumps({"session_id": session_id, "mode": mode}),
    }
