"""Apify read client for the X (Twitter) Skills project.

The read layer: given a handle or a niche query, pull tweets with their author
and engagement so a skill can see what is working, who is engaging, and how a
competitor performs. Uses the run-sync-get-dataset-items endpoint (one HTTP
request, no polling).

Auth: APIFY_TOKEN env var (or constructor arg). Get one at
https://console.apify.com/account/integrations (free tier included).

Actor (verified live 2026-07-14): xquik/x-tweet-scraper. Accepts twitterHandles,
searchTerms, startUrls (tweet/profile/search URLs), or tweetIds, and returns
tweets with author {userName, followers}, likeCount, replyCount, viewCount,
conversationId, isReply, createdAt. ~$0.15 per 1,000 tweets, no cookies.

What X does NOT expose reliably: the list of who LIKED a tweet (X gates
like-visibility). The engagement signal here is REPLIERS and tweet performance,
not likers. That is a platform wall, not a client limitation.

Caching: in-process LRU (256 entries, 6h TTL). force_refresh=True to bypass.
Retries transient 429/5xx (3 attempts, exponential backoff + jitter).
"""
from __future__ import annotations
import os
import random
import time
from collections import OrderedDict
from typing import Any, Optional

import requests

ACTOR = "xquik~x-tweet-scraper"
RUN_SYNC = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
CACHE_MAX_ENTRIES = 256
CACHE_TTL_SECONDS = 6 * 60 * 60
SIGNUP_URL = "https://console.apify.com/account/integrations"


class ApifyError(RuntimeError):
    pass


class ApifyAuthError(ApifyError):
    """No token configured. Message explains the free path + paste fallback."""


def _retry(attempts: int = 3, base_delay: float = 0.6):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            last: Optional[Exception] = None
            for i in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except ApifyError as e:
                    if getattr(e, "status", None) not in RETRYABLE_STATUSES or i == attempts - 1:
                        raise
                    last = e
                    time.sleep(base_delay * (2 ** i) + random.uniform(0, 0.3))
            if last:
                raise last
        return wrapper
    return decorator


def _tweet(t: dict) -> dict:
    au = t.get("author") or {}
    return {
        "id": t.get("id"),
        "text": t.get("text") or t.get("fullText"),
        "author": au.get("username") or au.get("screen_name"),
        "author_name": au.get("name"),
        "author_followers": au.get("followers"),
        "likes": t.get("likeCount", 0),
        "replies": t.get("replyCount", 0),
        "reposts": t.get("retweetCount", t.get("quoteCount", 0)),
        "views": t.get("viewCount"),
        "is_reply": t.get("isReply", False),
        "conversation_id": t.get("conversationId"),
        "created_at": t.get("createdAt"),
        "url": (f"https://x.com/{au.get('username')}/status/{t.get('id')}"
                if au.get("username") and t.get("id") else None),
    }


class ApifyClient:
    def __init__(self, token: Optional[str] = None, timeout: int = 120):
        self.token = token or os.environ.get("APIFY_TOKEN")
        self.timeout = timeout
        self._cache: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()

    def _require(self) -> str:
        if not self.token:
            raise ApifyAuthError(
                "No APIFY_TOKEN set. Get one free at "
                f"{SIGNUP_URL}. Or paste the tweets/replies you already have and "
                "the skill will run the same analysis on them."
            )
        return self.token

    def _cget(self, k):
        h = self._cache.get(k)
        if h and (time.time() - h[0]) < CACHE_TTL_SECONDS:
            self._cache.move_to_end(k)
            return h[1]
        return None

    def _cput(self, k, v):
        self._cache[k] = (time.time(), v)
        self._cache.move_to_end(k)
        while len(self._cache) > CACHE_MAX_ENTRIES:
            self._cache.popitem(last=False)

    @_retry()
    def _run(self, payload: dict) -> list[dict]:
        try:
            r = requests.post(RUN_SYNC.format(actor=ACTOR),
                              params={"token": self._require()}, json=payload,
                              timeout=self.timeout)
        except requests.RequestException as e:
            err = ApifyError(f"network error: {e}"); err.status = 503; raise err
        if r.status_code >= 400:
            err = ApifyError(f"actor returned {r.status_code}: {r.text[:200]}")
            err.status = r.status_code; raise err
        data = r.json()
        if not isinstance(data, list):
            raise ApifyError(f"unexpected response shape: {str(data)[:150]}")
        # the actor emits a single diagnostic object when the input is empty/invalid
        if data and isinstance(data[0], dict) and data[0].get("resultType") == "diagnostic":
            raise ApifyError(f"actor diagnostic: {data[0].get('message')}")
        return data

    # ---- public read methods ----
    def fetch_user_tweets(self, handle: str, max_items: int = 30,
                          force_refresh: bool = False) -> list[dict]:
        """A handle's recent tweets (self or competitor). Verified path."""
        h = handle.lstrip("@")
        ck = f"user:{h}:{max_items}"
        if not force_refresh and (c := self._cget(ck)) is not None:
            return c
        rows = self._run({"twitterHandles": [h], "maxItems": max_items, "sort": "Latest"})
        out = [_tweet(t) for t in rows if isinstance(t, dict) and t.get("id")]
        self._cput(ck, out)
        return out

    def fetch_niche_top(self, query: str, max_items: int = 30, sort: str = "Top",
                        force_refresh: bool = False) -> list[dict]:
        """Top/latest tweets for a niche query. Search reliability on X varies;
        prefer fetch_user_tweets on known accounts when search returns nothing."""
        ck = f"search:{query}:{max_items}:{sort}"
        if not force_refresh and (c := self._cget(ck)) is not None:
            return c
        rows = self._run({"searchTerms": [query], "maxItems": max_items, "sort": sort})
        out = [_tweet(t) for t in rows if isinstance(t, dict) and t.get("id")]
        self._cput(ck, out)
        return out

    def fetch_tweet_replies(self, tweet_url: str, max_items: int = 50,
                           force_refresh: bool = False) -> list[dict]:
        """Replies on a tweet (the X engagement signal, since likers are gated).
        Pulls the conversation via the tweet URL and keeps the replies."""
        ck = f"replies:{tweet_url}:{max_items}"
        if not force_refresh and (c := self._cget(ck)) is not None:
            return c
        rows = self._run({"startUrls": [tweet_url], "maxItems": max_items})
        out = [_tweet(t) for t in rows if isinstance(t, dict) and t.get("id") and t.get("isReply")]
        self._cput(ck, out)
        return out


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(ApifyClient().fetch_user_tweets("naval", 3), indent=2))
