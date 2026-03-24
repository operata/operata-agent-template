#!/usr/bin/env python3
"""Validate environment setup for the agent.

Checks that required credentials and services are accessible.
Run directly or via `make check`.
"""

import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
warned = 0
failed = 0


def ok(msg: str):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg: str):
    global warned
    warned += 1
    print(f"  {YELLOW}⚠{RESET} {msg}")


def fail(msg: str):
    global failed
    failed += 1
    print(f"  {RED}✗{RESET} {msg}")


# ── Python version ──────────────────────────────────────────────────────────

print(f"\n{BOLD}Python{RESET}")
v = sys.version_info
if v >= (3, 10):
    ok(f"Python {v.major}.{v.minor}.{v.micro}")
else:
    fail(f"Python {v.major}.{v.minor}.{v.micro} — requires 3.10+")

# ── AWS credentials ─────────────────────────────────────────────────────────

print(f"\n{BOLD}AWS{RESET}")

region = os.environ.get("AWS_REGION", "")
if region:
    ok(f"AWS_REGION={region}")
else:
    warn("AWS_REGION not set (will default to us-west-2)")

try:
    import boto3

    sts = boto3.client("sts", region_name=region or "us-west-2")
    identity = sts.get_caller_identity()
    account = identity["Account"]
    arn = identity["Arn"]
    ok(f"AWS credentials valid — account {account}")
    ok(f"Identity: {arn}")
except Exception as e:
    fail(f"AWS credentials: {e}")

# ── Slack ───────────────────────────────────────────────────────────────────

print(f"\n{BOLD}Slack{RESET}")

slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
if slack_token:
    try:
        import requests

        resp = requests.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {slack_token}"},
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            ok(f"Slack bot token valid — bot: {data.get('user', 'unknown')} in team: {data.get('team', 'unknown')}")
        else:
            fail(f"Slack auth.test failed: {data.get('error', 'unknown')}")
    except Exception as e:
        fail(f"Slack connection failed: {e}")
else:
    warn("SLACK_BOT_TOKEN not set — Slack tools disabled")

# ── Optional integrations ───────────────────────────────────────────────────

print(f"\n{BOLD}Optional integrations{RESET}")

memory_id = os.environ.get("AGENTCORE_MEMORY_ID", "")
if memory_id:
    ok(f"AGENTCORE_MEMORY_ID={memory_id}")
else:
    warn("AGENTCORE_MEMORY_ID not set — run `python tools/memory_tools.py` to create")

# TODO: Add checks for your data sources here. Examples:
#
# jira_token = os.environ.get("JIRA_API_TOKEN", "")
# if jira_token:
#     ok("JIRA_API_TOKEN set")
# else:
#     warn("JIRA_API_TOKEN not set — Jira tools disabled")
#
# github_token = os.environ.get("GITHUB_TOKEN", "")
# if github_token:
#     ok("GITHUB_TOKEN set")
# else:
#     warn("GITHUB_TOKEN not set — GitHub tools disabled")

# ── Summary ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}Summary{RESET}")
total = passed + warned + failed
print(f"  {GREEN}{passed} passed{RESET}  {YELLOW}{warned} warnings{RESET}  {RED}{failed} failed{RESET}")

if failed > 0:
    print(f"\n  {RED}Fix the failures above before running the agent.{RESET}")
    print("  See .env.example for required configuration.\n")
    sys.exit(1)
elif warned > 0:
    print(f"\n  {YELLOW}Agent will run with reduced capabilities.{RESET}")
    print("  Optional integrations can be enabled in .env\n")
    sys.exit(0)
else:
    print(f"\n  {GREEN}All checks passed. Ready to run!{RESET}\n")
    sys.exit(0)
