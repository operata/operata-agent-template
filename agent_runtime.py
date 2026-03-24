"""Agent — AgentCore Runtime Entry Point.

Wraps agent modes behind a single BedrockAgentCoreApp entrypoint.
Dispatches based on the ``mode`` field in the invocation payload:

    {"mode": "default"}                     → primary agent mode
    {"mode": "default", "dry_run": true}    → primary mode without writes

Existing agent.py continues to work unchanged for local dev.
"""

import json
import logging
import os
from datetime import datetime, timezone

from bedrock_agentcore.runtime import BedrockAgentCoreApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context=None):
    """AgentCore invocation handler — dispatches to the appropriate mode."""
    if isinstance(payload, (str, bytes)):
        payload = json.loads(payload)

    mode = payload.get("mode", "default")
    dry_run = payload.get("dry_run", False)

    # Set DRY_RUN before importing agent modules (they read it at module level)
    if dry_run:
        os.environ["DRY_RUN"] = "true"
    else:
        os.environ.pop("DRY_RUN", None)

    logger.info("Invoked: mode=%s, dry_run=%s", mode, dry_run)

    if mode == "default":
        from agent import run

        result = run()
        return {
            "mode": "default",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": _extract_text(result),
        }

    # TODO: Add additional modes here. Example:
    # elif mode == "triage":
    #     from agent_triage import triage
    #     result = triage(payload.get("ticket_key"))
    #     return {"mode": "triage", "message": _extract_text(result)}

    return {"error": f"Unknown mode: {mode}"}


def _extract_text(result):
    """Pull the text content from a Strands agent result."""
    try:
        return result.message["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return str(result)


if __name__ == "__main__":
    app.run()
