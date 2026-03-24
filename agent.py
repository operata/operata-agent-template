"""Agent — Primary Mode.

TODO: Update the docstring to describe what this agent does.
"""

import argparse
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent

from agent_config import DRY_RUN, MODEL, SYSTEM_PROMPT, build_tools
from tools.memory_tools import create_memory_session

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def run():
    """Run the agent's primary mode."""
    dry_run = DRY_RUN or os.environ.get("DRY_RUN", "false").lower() == "true"
    today = datetime.now().strftime("%Y-%m-%d")
    session_manager = create_memory_session(session_id=f"run-{today}")

    agent = Agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=build_tools(dry_run=dry_run, mode="default"),
        session_manager=session_manager,
    )

    # TODO: Write the prompt that drives this agent's primary behaviour.
    # Be specific about what to query, how to format results, and where to post.
    prompt = (
        f"Today is {today}. "
        f"TODO: Replace this with the agent's primary task prompt. "
    )

    if dry_run:
        prompt += "This is a DRY RUN — do not post to Slack or write to external systems. Print the output to stdout only."
    else:
        prompt += (
            "TODO: Add instructions for live mode — where to post results, "
            "what to write, and any guardrails."
        )

    result = agent(prompt)

    # Save output as markdown and open in VS Code
    text = _extract_text(result)
    output_path = _save_output(text, f"output-{today}", dry_run)
    print(f"\n{'=' * 60}")
    print(f"Run completed: {today}")
    print(f"Output saved: {output_path}")
    print(f"{'=' * 60}")
    return result


def _extract_text(result):
    """Pull the text content from a Strands agent result."""
    try:
        return result.message["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return str(result)


def _save_output(text: str, name: str, dry_run: bool) -> Path:
    """Save agent output as markdown and open in VS Code."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = "dry-run" if dry_run else "live"
    filename = f"{name}-{prefix}-{timestamp}.md"
    output_path = output_dir / filename

    output_path.write_text(text, encoding="utf-8")

    # Auto-open in VS Code if available
    try:
        subprocess.Popen(["code", str(output_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass  # VS Code CLI not available

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TODO: Agent description")
    parser.add_argument("--dry-run", action="store_true", help="Suppress external writes")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    run()
