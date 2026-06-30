"""Approval gate helpers.

Every skill that posts to X MUST present a draft to the user and wait for
explicit approval before calling Publora. This file is a thin conventions
layer, not runtime enforcement. Skills call `render_approval_card` to format
the draft consistently and then stop until the user says go.
"""
from __future__ import annotations
from typing import Optional


def render_approval_card(
    *,
    kind: str,  # "post" | "thread" | "reply" | "quote"
    preview_text: str,
    target_url: Optional[str] = None,
    char_count: Optional[int] = None,
    tweet_count: Optional[int] = None,
    extra_context: Optional[dict] = None,
) -> str:
    """Format a standardized approval card for the user to review.

    The card MUST contain:
    - What the action is (post / thread / reply / quote)
    - The full preview text
    - Char count, and tweet count for threads
    - Target URL if applicable (the tweet being replied to / quoted)
    - A clear prompt: "reply post / yes to publish, or suggest edits"
    """
    lines = [f"## Draft ready for approval - {kind}", ""]
    if target_url:
        lines.append(f"**Target:** {target_url}")
    if char_count is None:
        char_count = len(preview_text)
    lines.append(f"**Chars:** {char_count}")
    if tweet_count is not None:
        lines.append(f"**Tweets:** {tweet_count}")
    lines.append("")
    lines.append("**Preview:**")
    lines.append("")
    for pl in preview_text.splitlines() or [""]:
        lines.append(f"> {pl}")
    lines.append("")
    if extra_context:
        lines.append("**Context:**")
        for k, v in extra_context.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    lines.append("Reply **post** / **yes** to publish, or suggest edits.")
    return "\n".join(lines)
