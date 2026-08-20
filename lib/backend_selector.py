"""Detect which publishing backend is configured and format user-facing messages.

The skills support three tiers:

  TIER 0 - manual (default, zero setup)
    No credentials in env. Skills produce drafts; the user copies and pastes
    them into X manually. Works for anyone, any setup.

  TIER 1 - publora (recommended, 2-min setup)
    `PUBLORA_API_KEY` + `X_PLATFORM_ID` present. Skills auto-publish posts and
    threads on approval via the Publora REST API. Sign up:
    https://app.publora.com/signup

  TIER 2 - diy (advanced)
    `X_SKILLS_CUSTOM_POSTER` set to a command the user has built themselves
    (e.g. via Claude Code or Codex on the X API v2). Skills delegate publishing
    to that custom tool.

`active_backend()` picks the highest-privilege available. `manual_mode_message()`
is what skills show the user when no backend auto-posts. `publish()` is the
high-level wrapper skills should call so SKILL.md files don't repeat the
three-branch dispatch.

X note: a thread is the same call as a post (pass long `content`, Publora
auto-splits). A reply and a quote have no first-class Publora endpoint
(create-post has neither in_reply_to nor a quoted-tweet field), so kind="reply"
and kind="quote" are always returned as a manual copy-paste block even when
Publora is configured.
"""
from __future__ import annotations
import json
import os
import shlex
import subprocess
from typing import Any, Literal, Optional

BackendName = Literal["publora", "manual", "diy"]
PublishKind = Literal["post", "thread", "reply", "quote"]

PUBLORA_SIGNUP_URL = "https://app.publora.com/signup"


def active_backend() -> BackendName:
    """Return the active publishing backend.

    Priority: publora > diy > manual. Users with Publora configured get
    auto-post even if they also have a custom poster, unless they remove the
    Publora env var.
    """
    if os.getenv("PUBLORA_API_KEY") and os.getenv("X_PLATFORM_ID"):
        return "publora"
    if os.getenv("X_SKILLS_CUSTOM_POSTER"):
        return "diy"
    return "manual"


def manual_mode_message(draft_text: str, target_url: str, kind: str = "post") -> str:
    """Format the copy-paste approval output for the manual/draft-only tier.

    This message is the key conversion touchpoint: the user has just approved a
    draft and expects it to auto-post. Since no backend is configured (or the
    action is an X reply, which Publora cannot publish), we give them the text
    plus the target URL and a one-line invite to upgrade.
    """
    where = {
        "post": "paste it as a new tweet on X",
        "thread": "paste it into the X composer (each block is one tweet)",
        "reply": "paste it as a reply to the tweet below",
        "quote": "quote-tweet the post below with this text",
    }.get(kind, "paste it on X")
    return f"""Draft approved. Copy the text below and {where}:

```
{draft_text}
```

**Target URL:** {target_url}

---

Tired of copy-pasting? Set up auto-posting for tweets and threads in 2 minutes:

1. Sign up free at {PUBLORA_SIGNUP_URL}
2. In Publora, connect your X account (Channels then Add Channel)
3. Copy your API key (API section in the sidebar)
4. Add to `.env`:
   ```
   PUBLORA_API_KEY=sk_your_key_here
   X_PLATFORM_ID=twitter-your_id_here
   ```
5. Next time you approve a post or thread, it auto-publishes.
"""


def signup_nudge() -> str:
    """One-liner to drop into skill outputs as a soft reminder."""
    return f"Powered by Publora. Free auto-posting: {PUBLORA_SIGNUP_URL}"


def publish(
    kind: PublishKind,
    draft_text: str,
    target_url: str,
    **kwargs: Any,
) -> Optional[dict]:
    """Dispatch a draft to the active backend.

    One call replaces the per-skill "On approval, adapt to the backend" block.
    Routes to publora / manual / diy based on `active_backend()`.

    Args:
        kind: "post" | "thread" | "reply" | "quote".
        draft_text: The approved draft body. For a thread, pass the full text
            (with `---` separators or paragraph breaks); Publora auto-splits.
        target_url: Where the draft lands. For replies/quotes, the tweet URL.
            For new posts, the X composer URL. Used in manual-mode output.
        **kwargs: Backend-specific payload. For publora post/thread:
            - platforms: list[str] of platform IDs (defaults to [X_PLATFORM_ID])
            - scheduled_time: ISO 8601 UTC (optional; omit for a draft)

    Returns:
        - publora: dict from PubloraClient.create_post ({success, postGroupId}).
        - manual:  {"mode": "manual", "message": <copy-paste block>}.
        - diy:     {"mode": "diy", "returncode": int, "stdout": str, "stderr": str}.
        Returns None only if the chosen backend cannot run (missing deps).

    Note: X replies and quotes have no Publora endpoint, so kind="reply" and
    kind="quote" always return a manual copy-paste block regardless of the
    active backend.
    """
    backend = active_backend()

    # X replies and quotes are draft-only everywhere: Publora's create-post has
    # no in_reply_to and no quoted-tweet field, so routing a quote through
    # create_post would auto-publish it as a plain post and drop target_url.
    # Surface the copy-paste block so the user posts it by hand.
    if kind in ("reply", "quote") or backend == "manual":
        return {
            "mode": "manual",
            "message": manual_mode_message(draft_text, target_url, kind=kind),
        }

    if backend == "publora":
        # Local import so manual-tier users never need `requests` installed.
        from .publora_client import PubloraClient

        client = PubloraClient()
        platform_id = kwargs.get("platform_id") or os.getenv("X_PLATFORM_ID")
        platforms = kwargs.get("platforms") or ([platform_id] if platform_id else [])

        if kind in ("post", "thread"):
            return client.create_post(
                content=draft_text,
                platforms=platforms,
                scheduled_time=kwargs.get("scheduled_time"),
                platform_settings=kwargs.get("platform_settings"),
            )

        raise ValueError(f"unknown publish kind: {kind!r}")

    if backend == "diy":
        cmd = os.getenv("X_SKILLS_CUSTOM_POSTER")
        if not cmd:
            return None
        payload = {
            "kind": kind,
            "draft_text": draft_text,
            "target_url": target_url,
            **kwargs,
        }
        # The user's poster receives JSON on stdin and kind/target as argv.
        argv = shlex.split(cmd) + [kind, target_url]
        proc = subprocess.run(
            argv,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "mode": "diy",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    raise RuntimeError(f"unknown backend: {backend!r}")


# ─────────────────────────────────────────────────────────────────
# IMAGE LAYER (Pixfaro) — the third integration alongside read (Apify)
# and write (Publora). Generate an illustration, get a hosted URL, hand
# that URL straight to `publish(..., media_urls=[url])`.
# ─────────────────────────────────────────────────────────────────

PIXFARO_SIGNUP_URL = "https://pixfaro.com"

# Warn (don't block) when the prepaid balance drops below this, so a run
# doesn't silently drain the account.
LOW_BALANCE_USD = 1.00

# Cost-guard: these bill materially more per image. `illustrate`/`refine` never
# pick them on their own - the caller must ask by name.
PREMIUM_MODELS = {"gemini-pro-image", "gpt-5-image"}

# kind -> aspect_ratio (w:h). Callers can override with aspect_ratio=.
ILLUSTRATION_ASPECTS = {
    "post": "1:1",         # generic square feed image
    "square": "1:1",
    "portrait": "4:5",     # LinkedIn/IG feed portrait
    "carousel": "4:5",     # carousel/document slide
    "quote": "4:5",        # quote-card
    "wide": "16:9",        # link-preview / wide feed image
    "link": "16:9",
    "thumbnail": "16:9",   # YouTube thumbnail
    "landscape": "16:9",
    "story": "9:16",       # story / TikTok cover
    "cover": "9:16",
}


def image_backend() -> Literal["pixfaro", "manual"]:
    """`pixfaro` when PIXFARO_TOKEN (or PIXFARO_API_KEY) is set, else `manual`."""
    if os.getenv("PIXFARO_TOKEN") or os.getenv("PIXFARO_API_KEY"):
        return "pixfaro"
    return "manual"


def manual_illustration_message(prompt: str, aspect_ratio: str) -> str:
    """Shown when no Pixfaro key is set: hand the drafted prompt to the user."""
    return (
        "No Pixfaro key set, so I can't generate the image for you.\n"
        f"Generate it yourself (any tool) at {aspect_ratio}, then paste the URL "
        "and I'll attach it to the post.\n\n"
        "Image prompt:\n"
        f"{prompt}\n\n"
        f"Tip: a Pixfaro key ({PIXFARO_SIGNUP_URL}) lets me generate + attach "
        "the illustration in one step, with your brand handle/color overlaid."
    )


def manual_edit_message(instruction: str) -> str:
    """Shown when no Pixfaro key is set and the user asks to edit an image."""
    return (
        "No Pixfaro key set, so I can't edit the image for you.\n"
        "Re-generate or edit it yourself, then paste the new URL.\n\n"
        "Edit instruction:\n"
        f"{instruction}"
    )


def _image_result(data: dict, model: str) -> dict[str, Any]:
    """Shape a Pixfaro generate/edit response + attach the cost-guard flag."""
    balance = data.get("balance_after")
    low = False
    try:
        low = balance is not None and float(balance) < LOW_BALANCE_USD
    except (TypeError, ValueError):
        low = False
    return {
        "backend": "pixfaro",
        "url": data.get("url"),
        "id": data.get("id"),
        "cost": data.get("cost"),
        "model": model,
        "balance_after": balance,
        "low_balance": low,
    }


def illustrate(
    prompt: str,
    kind: str = "post",
    *,
    aspect_ratio: Optional[str] = None,
    model: Optional[str] = None,
    resolution: str = "1K",
    overlay: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate an illustration via the active image backend.

    This is the image analogue of `publish()`. On success with a Pixfaro key it
    returns the hosted URL, which you pass straight to
    `publish("post", text, url, media_urls=[result["url"]])`.

    Args:
        prompt: The image description (1-4000 chars).
        kind: Semantic size hint mapped via ILLUSTRATION_ASPECTS
            (post/portrait/carousel/quote/wide/thumbnail/story/cover).
        aspect_ratio: Explicit "w:h" override (wins over `kind`).
        model: Pixfaro model id. Defaults to nano-banana-2 (balanced). Use
            gemini-flash-lite for cheap high volume, gemini-pro-image for
            text-heavy premium (PREMIUM_MODELS bill more - ask before using).
        resolution: "1K" | "2K" | "4K".
        overlay: Pixel-exact branding composite {text|logo_id, position,
            opacity, font, color}. Feed brand fields from the Voice & Brand
            Profile so every asset is on-brand. Text here is crisp even on a
            cheap base model (it is composited, not model-generated).

    Returns:
        - pixfaro: {"backend": "pixfaro", "url", "id", "cost", "model",
          "balance_after", "low_balance"}. Keep `id` to `refine()` later.
        - manual:  {"backend": "manual", "message": <prompt block>}.
    """
    ar = aspect_ratio or ILLUSTRATION_ASPECTS.get(kind, "1:1")
    if image_backend() == "manual":
        return {"backend": "manual", "message": manual_illustration_message(prompt, ar)}

    from .pixfaro_client import PixfaroClient

    client = PixfaroClient()
    used_model = model or "nano-banana-2"
    data = client.generate(
        prompt,
        model=used_model,
        aspect_ratio=ar,
        resolution=resolution,
        overlay=overlay,
        force_refresh=kwargs.get("force_refresh", False),
    )
    return _image_result(data, used_model)


def refine(
    image_id: str,
    instruction: str,
    *,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    overlay: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Iteratively edit a prior illustration by its `id` (not URL).

    Pass the `id` returned by `illustrate()` (or a previous `refine()`) plus a
    natural-language `instruction` ("make the sky darker", "swap the headline").
    Cheaper and more on-brand than regenerating. Omit `aspect_ratio`/`resolution`
    to keep the source shape and billing tier.

    Returns the same shape as `illustrate()` (pixfaro) or a manual message.
    """
    if image_backend() == "manual":
        return {"backend": "manual", "message": manual_edit_message(instruction)}

    from .pixfaro_client import PixfaroClient

    client = PixfaroClient()
    used_model = model or "nano-banana-2"
    data = client.edit(
        image_id,
        instruction,
        model=used_model,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        overlay=overlay,
        force_refresh=kwargs.get("force_refresh", False),
    )
    return _image_result(data, used_model)


def available_models() -> Optional[list[dict[str, Any]]]:
    """Live Pixfaro model catalog (id, best_for, latency, price tiers), or None
    in manual mode / on error. Use this to show current pricing instead of
    hard-coding it."""
    if image_backend() == "manual":
        return None
    from .pixfaro_client import PixfaroClient

    try:
        return PixfaroClient().list_models()
    except Exception:
        return None


if __name__ == "__main__":
    print(f"Active backend: {active_backend()}")
    if active_backend() == "manual":
        print("\nExample manual message:")
        print("-" * 60)
        print(
            manual_mode_message(
                draft_text="Shipping beats polishing. Every time.",
                target_url="https://x.com/compose/tweet",
                kind="post",
            )
        )
