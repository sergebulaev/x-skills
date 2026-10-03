# Story Bank

The raw material your X posts are made of: what you have actually done, in
numbers, with names and dates. The Voice Profile holds *how you sound*. This holds
*what you have to say*.

Every writing skill in this bundle reads it before drafting, so it stops asking you
for "a specific number or moment" on every single request and starts drawing from
what you already told it once.

On X the sections that earn the most are Receipts and Positions: a figure
nobody else can quote, and a claim somebody will argue with in the replies.

> **Keep this out of git.** It holds career detail, figures, failures and named
> people. It is a file in this repository, so a push carries it wherever you push,
> a public fork included. Add `references/story-bank.md` to your `.gitignore`
> before you fill it, or keep the filled copy outside the repo. Nothing here is
> sent to us or to any service; git is the only way it travels.

Fill it by running `x-humanizer --mode interview`, which interviews you and writes
this file. You can also edit it by hand at any time; the skill reads whatever is here.

## Status

- filled: no
- updated: (date)
- sessions: (how many interviews have contributed)

---

## 1. What you are building now

The current thing, in enough detail to tweet about on any given day. X pays
attention to work in progress, so this section goes stale fastest and is worth
re-reading before a week of posting.

- (...)

## 2. Receipts

The numbers you can state without checking. This is the section drafts reach for
most, because one odd-precision figure with a named referent is the single
strongest signal that a human wrote the post.

Good: "cut deploy time from 22 minutes to 9, team of four, Q2 2025".
Useless: "improved efficiency significantly".

- (number, what it measures, when, who or what it belongs to)

## 3. Shipped

Things that exist because you worked on them. Products, migrations, hires, papers,
events, rescues.

- (what it was, your part in it, what it cost or returned)

## 4. Turning points

The moments where you changed your mind or the plan changed under you. These carry
posts better than successes do, and they are the hardest to invent.

- (what happened, what you believed before, what you believe now)

## 5. Scars

What went wrong and what it taught you. Kept separate from turning points because
the shape differs: a scar is a cost you paid, not a view you revised.

- (what broke, the real cost, what you do differently)

## 6. Positions

Opinions you would defend in a room that disagreed. A position with no cost to
holding it is not a position; note what holding it costs you.

- (the claim, who disagrees, why you hold it anyway)

## 7. Recurring stories

The three or four you already tell out loud, at dinner or in interviews. They are
proven: you know they land. Write them here before a draft dulls them.

- (the story in two lines, and the point it makes)

## 8. Names you can use

People, companies, tools and places you are free to name in public, and the ones
you are not. Drafts stay vague when they do not know which is which.

- Free to name: (...)
- Never name: (...)
- Ask first: (...)

## 9. Off limits

Subjects that stay out of posts regardless of how well they would perform: active
deals, litigation, health, other people's business, anything under NDA.

- (...)


---

## How drafts use this

- A draft needs a concrete detail: it takes one from **Receipts** or **Shipped**
  rather than asking you mid-session.
- A hook needs a reversal or a confession: **Turning points** and **Scars** are
  where those live.
- A post needs an argument: **Positions** supplies the claim and the opposition.
- Anything a draft cannot source from here, it asks about or leaves out. It does
  not invent a number. If you see an unfamiliar figure in a draft, that is a bug
  worth reporting.
