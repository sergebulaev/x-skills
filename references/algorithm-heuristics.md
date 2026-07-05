# 2026 X (Twitter) Posting Heuristics

Synthesized from the open-sourced X recommendation algorithm (the
`the-algorithm` repo and its 2024-2026 updates), public statements from the X
engineering account, and observed creator data. Numbers marked "reported" are
community-measured, not officially confirmed.

## Contents

- Signal weights (relative reach impact)
- The first 30-60 minutes
- Reach suppressors (avoid)
- Reach amplifiers
- Character and format limits
- Threads
- Reply vs quote tweet
- Timing
- Bookmarks are the underrated lever
- Pre-publish checklist

## Signal weights (relative reach impact)

X's ranker scores predicted engagement, and the engagement types are not equal.
Reported relative weights from the open algorithm and creator testing:

| Signal | Relative weight | Note |
|---|---|---|
| **Reply** (esp. with author reply back) | highest positive | a real conversation is the strongest signal |
| **Repost** | high | re-injects into a new follower graph |
| **Profile click then engage** | high | "this account is worth following" signal |
| **Bookmark** | high (added 2024) | private save, correlates with reference-worthy content |
| **Long dwell / "Show more" expand** | medium-high | reading the whole thing counts |
| **Video completion (50%+)** | medium-high | for video tweets |
| **Like** | low | cheap affirmation, light reach |
| **Negative: "Not interested", mute, block, report** | heavy penalty | one report outweighs many likes |

Takeaway: optimize the first tweet for **replies, reposts, and bookmarks**, not
likes. Likes are social proof for the next reader but barely move distribution.

## The first 30-60 minutes

- The opening window sets the trajectory. Early replies and reposts tell the
  ranker to widen distribution.
- **Reply to early replies fast.** Author engagement back on a reply is a strong
  signal and pulls the conversation up the thread.
- 3+ substantive replies in the first 30 minutes earns a second distribution
  test.

## Reach suppressors (avoid)

- **External links in the tweet body** suppress reach. X wants users to stay on
  platform. Put the link in a reply to your own tweet, or in tweet 2+ of a
  thread, not in tweet 1.
- **Engagement bait** ("RT if you agree", "reply YES") is downranked, not
  rewarded.
- **Repeated near-duplicate posts** (same tweet reworded) trip a similarity
  penalty.
- **High mute/block/report rate** collapses distribution fast and is slow to
  recover from.
- **Too many hashtags.** Zero or one is native; two or more reads as spam.

## Reach amplifiers

- **X Premium / verified** gets a reported reach boost and longer-tweet ability
  (25,000 chars, longer video). Replies from verified accounts also rank higher
  in the thread.
- **Native video** is favored. Upload to X directly; do not link out to YouTube.
- **Threads that get fully read** (deep tap-through) signal quality.
- **Conversation that the author keeps alive** by replying compounds reach over
  hours, not minutes.

## Character and format limits

| Item | Standard | X Premium |
|---|---|---|
| Tweet text | 280 chars | 25,000 chars |
| Images per tweet | 4 | 4 |
| Image size | 5 MB | 5 MB |
| Video length | 2 min (140s) | longer (plan tier dependent) |
| Video size (API) | 512 MB | 512 MB |

- **Emoji count as 2 characters** toward the 280 limit on X. A tweet that looks
  like 278 display chars can be over budget with two emoji.
- Publora reserves ~8 chars per tweet for the `(X/N)` thread marker when it
  auto-splits.

## Threads

- **Tweet 1 is the entire funnel.** It must promise a payoff and open a loop.
  Everything else only matters if tweet 1 earns the tap.
- **Front-load the value.** Tap-through decays with depth, so the strongest item
  or beat goes at position 1 or 2, not saved for the finale.
- **Optimal thread length: 5-9 tweets** for a teaching or list thread. Longer
  works for a strong story but tap-through keeps dropping.
- **Each tweet should stand alone** enough that a reader landing mid-thread from
  a quote tweet still gets value.
- **The last tweet earns the repost and the follow.** Close with the most
  quotable line, then a single clear ask (bookmark, follow, or "reply with
  yours"), not both.
- Publora auto-splits long `content` at paragraph breaks first, then sentence
  endings, then word boundaries, and numbers each tweet `(1/N)`. You can also
  hand-split with `---` separators for full control of where breaks land.

## Reply vs quote tweet

- **Reply** stays inside the original thread. Use it to add to a conversation,
  answer a question, or engage a creator. Lower reach, higher intimacy.
- **Quote tweet** creates a new post on your own timeline with the original
  embedded. Use it when your addition deserves its own reach and your followers
  should see the original for context. Higher reach, more public.
- X has **no LinkedIn-style 2-level thread flattening.** Replies nest naturally,
  and there is no special parent-comment URN to resolve. A reply is just a tweet
  posted in-reply-to another tweet.

## Timing

| Audience | Best windows (local) |
|---|---|
| US tech / builders / founders | Tue-Thu 9-11 AM ET, and a second bump 1-3 PM ET |
| Global mixed | weekday mornings in the audience timezone |
| Night-owl dev crowd | 8-11 PM also performs for build-in-public content |

- Weekdays beat weekends for B2B and tech. Weekend works for personal/relatable
  content and story threads.
- X moves faster than LinkedIn: a tweet's active life is hours, not a day. You
  can post more often (2-4 times a day is normal for an active account) without
  the cannibalization penalty LinkedIn imposes.

## Bookmarks are the underrated lever

- Bookmarks became a ranked signal in 2024 and reward **reference-worthy
  content**: lists, frameworks, hard numbers, repeatable how-tos.
- A bookmark is a stronger quality signal than a like because it means the
  reader intends to return.
- Design save-bait deliberately: the Mini-List (X5), Listicle-Thread (X7),
  How-I Teardown (X10), and Data-Point (X2) formulas all target bookmarks.

## Pre-publish checklist

- [ ] First tweet stops the scroll on its own (no fold to lean on).
- [ ] No em dashes (`—`), en dashes (`–`), or double dashes (`--`).
- [ ] No AI vocabulary blacklist words (leverage, fundamentally, delve, etc.).
- [ ] At least one specific number where the claim allows it.
- [ ] No external link in tweet 1 (move it to a reply or tweet 2+).
- [ ] 0 or 1 hashtag, at the end.
- [ ] 0-1 emoji, and only if it earns its place. None on a serious take.
- [ ] Single tweet under 280 chars (emoji = 2 each), or a deliberate thread.
- [ ] Thread tweet 1 opens a loop; the body closes it.
- [ ] Close is a landing or a specific ask, not "what do you think?".
- [ ] A clear primary goal (replies / reposts / likes / bookmarks), not all at once.
