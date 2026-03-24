"""Slack tools for posting agent output and reading channel history.

Posts using Slack Block Kit with auto-linked Jira tickets and @mentions.
Uses the Slack Web API directly.
"""

import json
import os
import re
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from strands import tool
from urllib3.util.retry import Retry

from config import JIRA_BASE_URL, JIRA_TICKET_PREFIXES, SLACK_CHANNEL_ENV_MAP

SLACK_BASE = "https://slack.com/api"
JIRA_BASE = JIRA_BASE_URL

# Resilient HTTP session with retry on transient failures
_session = requests.Session()
_retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=_retry))


def _slack_token():
    return os.environ.get("SLACK_BOT_TOKEN", "")


_CHANNEL_ENV_MAP = SLACK_CHANNEL_ENV_MAP


def _channels():
    return {name: os.environ.get(env, "") for name, env in _CHANNEL_ENV_MAP.items()}


def _slack_headers():
    return {"Authorization": f"Bearer {_slack_token()}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# User lookup for @mentions
# ---------------------------------------------------------------------------

_USER_CACHE: dict | None = None

# Guard against the LLM calling post_to_slack multiple times per run.
_POSTED_CHANNELS: set[str] = set()

_USERS_FILE = Path(__file__).parent.parent / "slack_users.json"


def _get_user_map() -> dict[str, str]:
    """Load user map from slack_users.json, then overlay with Slack API results."""
    global _USER_CACHE
    if _USER_CACHE is not None:
        return _USER_CACHE

    _USER_CACHE = {}

    if _USERS_FILE.exists():
        try:
            with open(_USERS_FILE) as f:
                data = json.load(f)
            for name, uid in data.items():
                if not name.startswith("_") and isinstance(uid, str):
                    _USER_CACHE[name] = uid
        except Exception:
            pass

    try:
        resp = _session.get(f"{SLACK_BASE}/users.list", headers=_slack_headers(), timeout=30)
        api_data = resp.json()
        if api_data.get("ok"):
            for member in api_data.get("members", []):
                if member.get("deleted") or member.get("is_bot") or member.get("id") == "USLACKBOT":
                    continue
                uid = member["id"]
                profile = member.get("profile", {})
                real_name = (profile.get("real_name") or "").strip()
                if real_name and " " in real_name and real_name not in _USER_CACHE:
                    _USER_CACHE[real_name] = uid
    except Exception:
        pass

    return _USER_CACHE


def _resolve_mentions(text: str) -> str:
    """Replace full user names with Slack <@UID> mentions."""
    user_map = _get_user_map()
    if not user_map:
        return text

    for name in sorted(user_map, key=len, reverse=True):
        uid = user_map[name]
        parts = re.split(r"(<[^>]+>)", text)
        text = "".join(
            part
            if part.startswith("<")
            else re.sub(r"\b" + re.escape(name) + r"\b", f"<@{uid}>", part, flags=re.IGNORECASE)
            for part in parts
        )
    return text


# ---------------------------------------------------------------------------
# Auto-link Jira tickets
# ---------------------------------------------------------------------------


def _auto_link_tickets(text: str) -> str:
    """Convert PROJ-XXXX to clickable Jira links. Skips already-linked references."""
    if not JIRA_TICKET_PREFIXES:
        return text

    def _repl(m):
        t = m.group(0)
        return f"<{JIRA_BASE}/browse/{t}|{t}>"

    prefix_pattern = "|".join(re.escape(p) for p in JIRA_TICKET_PREFIXES)
    parts = re.split(r"(<[^>]+>)", text)
    return "".join(
        part if part.startswith("<") else re.sub(rf"\b(?:{prefix_pattern})-\d+\b", _repl, part) for part in parts
    )


# ---------------------------------------------------------------------------
# Markdown → Slack mrkdwn + Block Kit
# ---------------------------------------------------------------------------

_NUM_EMOJI = {
    "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣",
    "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣",
}

_SKIP_LABELS = {"who", "assignee", "owner", "notes", "note", "comment", "comments", "description"}


def _md_to_mrkdwn(text: str) -> str:
    """Convert markdown inline formatting to Slack mrkdwn with links & mentions."""
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)  # bold
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", text)  # md links
    text = _auto_link_tickets(text)
    text = _resolve_mentions(text)
    return text


def _table_to_mrkdwn(table_lines: list[str]) -> str:
    """Convert a markdown table to compact Slack mrkdwn."""
    if len(table_lines) < 2:
        return ""

    raw_headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]

    rows: list[list[str]] = []
    for line in table_lines[1:]:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        rows.append(cells)
    if not rows:
        return ""

    is_kv = len(raw_headers) == 2 and len(re.sub(r"[*#_ ]", "", raw_headers[0])) < 3
    if is_kv:
        return "\n".join(f"{_md_to_mrkdwn(r[0])} {_md_to_mrkdwn(r[1]) if len(r) > 1 else ''}".strip() for r in rows)

    headers = [re.sub(r"[*#_]", "", h).strip() for h in raw_headers]
    out: list[str] = []

    for row in rows:
        cells = [_md_to_mrkdwn(c.strip()) for c in row]

        marker = "•"
        start = 0
        if headers and headers[0] in ("#", "") and cells:
            idx = cells[0].strip()
            if idx.isdigit():
                marker = _NUM_EMOJI.get(idx, f"*{idx}.*")
                start = 1
            elif len(idx) <= 2:
                start = 1

        rc = cells[start:]
        rh = headers[start:]
        if not rc or not any(rc):
            continue

        line1 = f"{marker}  {rc[0]}"
        if len(rc) > 1 and rc[1]:
            line1 += f" — {rc[1]}"

        meta = []
        for j in range(2, len(rc)):
            val = rc[j]
            if not val:
                continue
            label = rh[j] if j < len(rh) else ""
            if label.lower() in _SKIP_LABELS:
                meta.append(val)
            elif label:
                meta.append(f"_{label}:_ {val}")
            else:
                meta.append(val)

        out.append(line1)
        if meta:
            out.append("      " + "  ·  ".join(meta))

    return "\n".join(out)


def _flush_buffer(blocks: list[dict], buf: list[str]) -> None:
    """Emit buffered text as section blocks (≤3 000 chars each)."""
    text = "\n".join(buf).strip()
    buf.clear()
    if not text:
        return
    while text:
        if len(text) <= 3000:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
            break
        cut = text.rfind("\n", 0, 3000)
        if cut < 2000:
            cut = 3000
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text[:cut].rstrip()}})
        text = text[cut:].lstrip("\n")


def markdown_to_blocks(markdown: str) -> list[dict]:
    """Convert a full markdown document to Slack Block Kit blocks."""
    blocks: list[dict] = []
    lines = markdown.split("\n")
    buf: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if re.match(r"^# [^#]", stripped):
            _flush_buffer(blocks, buf)
            blocks.append(
                {"type": "header", "text": {"type": "plain_text", "text": stripped[2:].strip()[:150], "emoji": True}}
            )
        elif re.match(r"^## [^#]", stripped):
            _flush_buffer(blocks, buf)
            blocks.append(
                {"type": "header", "text": {"type": "plain_text", "text": stripped[3:].strip()[:150], "emoji": True}}
            )
        elif re.match(r"^### ", stripped):
            _flush_buffer(blocks, buf)
            buf.append(f"\n*{_md_to_mrkdwn(stripped[4:].strip())}*")
        elif stripped == "---":
            _flush_buffer(blocks, buf)
            blocks.append({"type": "divider"})
        elif stripped.startswith("|") and "|" in stripped[1:]:
            tbl: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            i -= 1
            converted = _table_to_mrkdwn(tbl)
            if converted:
                buf.append(converted)
        else:
            buf.append(_md_to_mrkdwn(line))

        i += 1

    _flush_buffer(blocks, buf)
    return blocks


# ---------------------------------------------------------------------------
# Slack API tools
# ---------------------------------------------------------------------------


@tool
def post_to_slack(channel_name: str, message: str) -> str:
    """Post a message to a Slack channel using Block Kit formatting.

    The message can use standard markdown — it is automatically converted
    to Slack Block Kit with clickable Jira links and @user mentions.

    Do NOT use this in dry-run mode.
    """
    if os.environ.get("DRY_RUN", "false").lower() == "true":
        return f"DRY RUN: Would have posted to #{channel_name}:\n{message[:200]}..."

    if channel_name in _POSTED_CHANNELS:
        return json.dumps(
            {
                "posted": False,
                "error": f"Already posted to #{channel_name} in this run. "
                "Compose the ENTIRE output as one message in a single call.",
            }
        )
    _POSTED_CHANNELS.add(channel_name)

    channel_id = _channels().get(channel_name, channel_name)
    all_blocks = markdown_to_blocks(message)
    fallback = _md_to_mrkdwn(message[:3000])

    main_blocks = all_blocks[:50]
    response = _session.post(
        f"{SLACK_BASE}/chat.postMessage",
        headers=_slack_headers(),
        json={"channel": channel_id, "text": fallback, "blocks": main_blocks, "unfurl_links": False},
    )
    data = response.json()
    if not data.get("ok"):
        return json.dumps({"posted": False, "error": data.get("error", "unknown")})

    ts = data.get("ts", "")

    if len(all_blocks) > 50:
        _session.post(
            f"{SLACK_BASE}/chat.postMessage",
            headers=_slack_headers(),
            json={
                "channel": channel_id,
                "thread_ts": ts,
                "text": "Continued…",
                "blocks": all_blocks[50:100],
                "unfurl_links": False,
            },
        )

    return json.dumps({"posted": True, "channel": channel_name, "ts": ts})


@tool
def read_slack_thread(channel_name: str, thread_ts: str) -> str:
    """Read replies to a previously posted Slack message.

    The thread_ts value comes from a previous post_to_slack call
    stored in the agent's memory.
    """
    channel_id = _channels().get(channel_name, channel_name)
    response = _session.get(
        f"{SLACK_BASE}/conversations.replies",
        headers=_slack_headers(),
        params={"channel": channel_id, "ts": thread_ts},
    )
    data = response.json()
    if not data.get("ok"):
        return json.dumps({"error": data.get("error", "unknown")})

    messages = []
    for msg in data.get("messages", [])[1:]:
        messages.append(
            {
                "user": msg.get("user", "unknown"),
                "text": msg.get("text", ""),
                "ts": msg.get("ts", ""),
            }
        )

    return json.dumps({"thread_ts": thread_ts, "reply_count": len(messages), "replies": messages})


@tool
def read_channel_history(channel_name: str, hours: int = 24, max_messages: int = 50) -> str:
    """Read recent messages from a Slack channel the bot is a member of.

    Args:
        channel_name: Channel name (must be in SLACK_CHANNEL_ENV_MAP in config.py)
        hours: How far back to look (default: 24 hours)
        max_messages: Maximum messages to return (default: 50, max: 100)
    """
    import time

    channel_id = _channels().get(channel_name, channel_name)
    if not channel_id:
        return json.dumps({"error": f"Unknown channel: {channel_name}. Use one of: {list(_channels().keys())}"})

    oldest = str(time.time() - (hours * 3600))
    max_messages = min(max_messages, 100)

    response = _session.get(
        f"{SLACK_BASE}/conversations.history",
        headers=_slack_headers(),
        params={"channel": channel_id, "oldest": oldest, "limit": max_messages},
    )
    data = response.json()
    if not data.get("ok"):
        return json.dumps({"error": data.get("error", "unknown"), "channel": channel_name})

    user_map = _get_user_map()
    uid_to_name = {uid: name for name, uid in user_map.items()}

    messages = []
    for msg in data.get("messages", []):
        if msg.get("subtype") in ("channel_join", "channel_leave", "bot_message"):
            continue
        uid = msg.get("user", "")
        messages.append(
            {
                "user": uid_to_name.get(uid, uid),
                "text": msg.get("text", "")[:500],
                "ts": msg.get("ts", ""),
                "thread_replies": msg.get("reply_count", 0),
            }
        )

    return json.dumps(
        {"channel": channel_name, "hours": hours, "message_count": len(messages), "messages": messages},
        indent=2,
    )
