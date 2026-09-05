# Voice Rules for X (Twitter)

These are the canonical voice rules for the whole bundle. Every skill inherits
them. Skill-local "Hard rules" sections only add format-specific overrides
(char ranges, threading rules) and point back here.

## Hard rules

1. **Em dashes (`—`) capped at one per tweet** (about 1 per 100 words in a
   long Premium post), and none in a tweet that reads fine without one. The
   character is no longer a tell (2026 models use fewer than humans); the
   density is, and on X em dashes are rare in top tweets (11% of our corpus).
   Replace the excess with a comma, colon or `..`, never a period. No en
   dashes (`–`) between clauses, no double dashes (`--`).
2. **Use `..` as a soft pause** when you would reach for a second em dash.
   Reads human and matches how people actually type on X.
3. **Capitalize personal names, company names, product names** (Stripe, Claude,
   Vercel). Lowercase a brand name and it reads as careless.
4. **Sentence starts can be lowercase.** Lowercase openers are native to X voice
   and often outperform capitalized ones. Names inside are always capitalized.
5. **Specific numbers beat adjectives.** 2.4x beats "way better". $873.47 beats
   "cheap". One real number per tweet where the claim allows it.
6. **One idea per tweet.** X punishes the comma-spliced run-on. If a tweet has
   two ideas, it is two tweets (or a thread).
7. **Don't hard-sell your own product** in a reply or a quote tweet on someone
   else's post. Describe what you do instead.

## Vocabulary markers (density-scored)

Count these per tweet. One is English; two is borderline (flag it in the report, leave the words);
three in one tweet reads as AI and the whole tweet gets rewritten (see `x-humanizer` V3).
The durable 2026 set (significant, crucial, notably, particularly,
comprehensive, insights, robust, leverage, foster, landscape, nuanced,
streamline, elevate, empower) counts alongside the older corporate words:
- leverage, utilize, facilitate, streamline, robust, seamless, delve, navigate,
  unlock, harness, foster, cultivate
- fundamentally, essentially, ultimately, crucially, notably
- landscape, ecosystem, paradigm, realm, tapestry, journey

## Always forbidden (single hit, regardless of density)

These are scrubbed on sight. They are reveal bridges, negative parallelism,
dead phrases or performed sincerity, not vocabulary:
- "It's not just X, it's Y"
- "In today's fast-paced world"
- "game-changer", "deep dive", "at the end of the day", "needle-mover"
- Sincerity announcements as an opener or pivot: "let me be honest", "I'll be
  real", "honestly?", "real talk", "not gonna lie", "unpopular opinion:" on a
  take that is actually popular. State the fact flat instead.

## X-native style

- **Lowercase-casual is a real register on X.** It signals you are a person, not
  a brand account. Use it when the voice calls for it; do not force it onto a
  serious or technical take.
- **Line breaks are punctuation.** A single hard return between two short lines
  reads as a beat. Use whitespace to control pacing inside a tweet.
- **Emoji: 0-1 per tweet, and only when it earns its place.** A thread that
  opens with one emoji is fine; a tweet sprinkled with 4 reads as a brand
  account or AI. Serious or contrarian takes use zero.
- **Hashtags: 0 or 1.** X does not need them for distribution in 2026, and 2 or
  more reads as spam. If you use one, put it at the end.

## Length

- **Standard account: 280 chars per tweet.** Write to land the whole idea inside
  it. A tweet that needs 290 chars needs an edit, not a second tweet.
- **X Premium: up to 25,000 chars** in a single tweet, but a wall of text still
  underperforms a tight one. Length is a ceiling, not a target. Reach for a
  thread before a 2,000-char monolith.
- **Thread tweets: keep each one able to stand alone.** A reader who lands on
  tweet 4 from a quote tweet should still get something.

## Structure

- The **first line of a single tweet, or tweet 1 of a thread, carries the whole
  load.** There is no "see more" fold on X. If the opener does not stop the
  scroll by itself, nothing downstream gets read.
- **End on a landing, not a dead prompt.** "What do you think?" is dead. A
  specific question, a sharp closing line, or a clean stop all beat it.
- For threads, **the last tweet earns the repost.** Close with the most
  quotable line or a clear call to bookmark/follow, not a limp "that's it".

## Anti-patterns

- Thesis restatement of someone else's tweet ("so true, X is changing
  everything").
- Generic praise in replies ("great thread!", "love this").
- Overused openers: "This.", "100%", "Couldn't agree more", "Unpopular opinion:"
  on a take that is actually popular.
- Stacked or hollow rule of three ("faster, cheaper, better"); one natural
  triple with concrete items is fine.
- Padding a one-line idea into a thread.
- ALL CAPS first lines for intensity. Carry intensity with word choice.

## Algorithmic note (NLP-level)

X's ranker reads the text and rewards genuine conversation. A tweet that earns
real replies (not one-word "this") and gets bookmarked outranks one that only
collects likes. Before posting, check: does this give a reader a reason to
reply, quote, or save? If it only earns a passive like, sharpen it.
