"""X (Twitter) URL parser.

Handles the common shapes for tweets and profiles on both hosts:

1. Tweet URL (from "Copy link"):
   https://x.com/HANDLE/status/TWEET_ID
   https://twitter.com/HANDLE/status/TWEET_ID
   ...with optional query params (?s=20&t=...) or a trailing /photo/1, /video/1.

2. Profile URL:
   https://x.com/HANDLE
   https://twitter.com/HANDLE

3. Bare numeric ID or i/web/status form:
   https://x.com/i/web/status/TWEET_ID

Returns a normalized dict:
    {
      "handle": "<screen_name>" | None,   # without the leading @
      "tweet_id": "<numeric>" | None,
      "url_type": "tweet" | "profile" | "unknown",
      "canonical_url": "https://x.com/..." | None,
    }

Note: X migrated from twitter.com to x.com but both hosts resolve. The parser
normalizes the canonical URL to x.com. A quote tweet is just a tweet URL; the
parser does not distinguish it (the reply-drafter skill decides reply vs quote
based on user intent, not the URL).
"""
from __future__ import annotations
import re
from typing import Optional, TypedDict
from urllib.parse import urlparse


class ParsedXUrl(TypedDict, total=False):
    handle: Optional[str]
    tweet_id: Optional[str]
    url_type: str
    canonical_url: Optional[str]


# Canonical registrable hosts X resolves on. A leading "www."/"m."/"mobile."
# is stripped before membership is checked, so those variants are covered too.
_X_HOSTS = {"x.com", "twitter.com"}
# Subdomain prefixes that point at the same canonical host.
_HOST_PREFIXES = ("www.", "m.", "mobile.")


def _registrable_host(text: str) -> str:
    """Extract the real host from a URL (with or without scheme), lowercased,
    with a leading www./m./mobile. stripped. Empty string if there is no host.

    Using urlparse here (instead of trusting the regex) is what blocks spoof
    hosts like vxtwitter.com, fxtwitter.com, mytwitter.com, and
    'evil.com/twitter.com/...': those carry a host that is not in `_X_HOSTS`.
    """
    # urlparse only fills netloc when a scheme (or leading //) is present.
    parsed = urlparse(text if "://" in text else "//" + text)
    host = (parsed.hostname or "").lower()
    for prefix in _HOST_PREFIXES:
        if host.startswith(prefix):
            return host[len(prefix):]
    return host

# /HANDLE/status/ID  (HANDLE may be a real handle or "i/web")
_STATUS_RE = re.compile(
    r"(?:https?://)?(?:[\w.]+\.)?(?:x|twitter)\.com/"
    r"(?P<handle>[A-Za-z0-9_]{1,15}|i/web)"
    r"/status(?:es)?/(?P<id>\d{5,25})",
    re.IGNORECASE,
)
# Profile URL: /HANDLE  (no /status)
_PROFILE_RE = re.compile(
    r"(?:https?://)?(?:[\w.]+\.)?(?:x|twitter)\.com/"
    r"(?P<handle>[A-Za-z0-9_]{1,15})/?(?:\?.*)?$",
    re.IGNORECASE,
)
# Reserved first-path segments that are not user handles.
_RESERVED = {
    "i", "home", "explore", "notifications", "messages", "search",
    "settings", "compose", "hashtag", "intent", "share", "login",
    "signup", "tos", "privacy",
}


def parse_x_url(url: str) -> ParsedXUrl:
    """Parse any X/Twitter tweet or profile URL into structured fields.

    >>> p = parse_x_url("https://x.com/paulg/status/1790000000000000000?s=20")
    >>> p["handle"]
    'paulg'
    >>> p["tweet_id"]
    '1790000000000000000'
    >>> p["url_type"]
    'tweet'
    """
    out: ParsedXUrl = {
        "handle": None,
        "tweet_id": None,
        "url_type": "unknown",
        "canonical_url": None,
    }
    if not url:
        return out

    text = url.strip()

    # Bare numeric tweet id with no host (e.g. pasted from an API). Handled
    # before host validation because it legitimately carries no host.
    if re.fullmatch(r"\d{5,25}", text):
        out["tweet_id"] = text
        out["url_type"] = "tweet"
        out["canonical_url"] = f"https://x.com/i/web/status/{text}"
        return out

    # Reject spoof hosts up front: only genuine x.com / twitter.com (and their
    # www./m./mobile. variants) are real X URLs. Anything else stays "unknown".
    if _registrable_host(text) not in _X_HOSTS:
        return out

    m = _STATUS_RE.search(text)
    if m:
        handle = m.group("handle")
        tweet_id = m.group("id")
        out["tweet_id"] = tweet_id
        if handle.lower() != "i/web":
            out["handle"] = handle
        out["url_type"] = "tweet"
        if out["handle"]:
            out["canonical_url"] = f"https://x.com/{out['handle']}/status/{tweet_id}"
        else:
            out["canonical_url"] = f"https://x.com/i/web/status/{tweet_id}"
        return out

    m = _PROFILE_RE.search(text)
    if m:
        handle = m.group("handle")
        if handle.lower() not in _RESERVED:
            out["handle"] = handle
            out["url_type"] = "profile"
            out["canonical_url"] = f"https://x.com/{handle}"
            return out

    return out


def build_tweet_url(handle: str, tweet_id: str) -> str:
    """Format a canonical x.com tweet URL from a handle and tweet id."""
    handle = handle.lstrip("@")
    return f"https://x.com/{handle}/status/{tweet_id}"


if __name__ == "__main__":
    import json
    import sys

    if sys.argv[1:]:
        examples = sys.argv[1:]
    else:
        examples = [
            "https://x.com/paulg/status/1790000000000000000?s=20",
            "https://twitter.com/naval/status/1002103360646823936",
            "https://x.com/levelsio",
            "https://x.com/i/web/status/1790000000000000000",
        ]

        # --- Host-validation self-test (spoofs must NOT parse as X) ---
        spoofs = [
            "https://vxtwitter.com/elonmusk/status/1790000000000000000",
            "https://fxtwitter.com/elonmusk/status/1790000000000000000",
            "https://mytwitter.com/elonmusk/status/1790000000000000000",
            "https://evil.com/twitter.com/x/status/1790000000000000000",
            "https://evil.com/x.com/levelsio",
        ]
        for s in spoofs:
            assert parse_x_url(s)["url_type"] == "unknown", f"spoof leaked: {s}"

        # Genuine URLs (incl. mobile.) must still parse.
        assert parse_x_url(
            "https://x.com/paulg/status/1790000000000000000?s=20"
        ) == {
            "handle": "paulg",
            "tweet_id": "1790000000000000000",
            "url_type": "tweet",
            "canonical_url": "https://x.com/paulg/status/1790000000000000000",
        }
        assert parse_x_url(
            "https://mobile.twitter.com/naval/status/1002103360646823936"
        )["url_type"] == "tweet"
        assert parse_x_url("https://x.com/levelsio")["url_type"] == "profile"
        assert parse_x_url("twitter.com/jack")["url_type"] == "profile"
        assert parse_x_url("1790000000000000000")["url_type"] == "tweet"
        print("self-test OK: spoof hosts rejected, real URLs parse\n")

    for u in examples:
        print(u)
        print(json.dumps(parse_x_url(u), indent=2))
        print()
