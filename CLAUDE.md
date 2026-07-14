# Project conventions - x-skills

This file is for any Claude Code agent working on this repository. Read it
before making changes. Conventions here are mandatory unless the user asks
otherwise.

## Versioning

- Single source of truth: `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, and
  `.agents/plugins/marketplace.json`. Plugin manifests must always match on
  package name and version; marketplace entries must point to the same package;
  author, license, homepage, and the public skill-bundle description must stay
  aligned.
- Keep `CLAUDE.md` and `AGENTS.md` aligned when changing shared project rules.
  Claude-specific workflow details belong here; Codex-specific details belong in
  `AGENTS.md`.
- Codex marketplace install uses `.codex-marketplace/x-skills/`. Do not edit that
  generated package by hand. Update the root files first, then run
  `python3 scripts/sync_codex_marketplace.py`.
- **Default: bump the PATCH segment (3rd level, `0.0.X`).** This is the automatic
  behavior for every shippable commit, regardless of how large the diff feels.
  Skill renames, lib API breaks, new features: still PATCH by default.
- Only bump MINOR or MAJOR when **the user explicitly asks** for a higher rank
  ("this is minor", "make it 2.0", "bump major"). Do not promote on your own
  initiative even if semver textbook says so.
- After bumping, two steps are required:
  1. Tag the commit: `git tag -a v<X.Y.Z> -m "..."` + `git push origin v<X.Y.Z>`
  2. **Publish a GitHub Release** for the tag: `gh release create v<X.Y.Z> --title "v<X.Y.Z>" --notes "<changelog>" --latest`
  A tag alone does NOT update the README release badge. The shields.io badge
  reads from the Releases API, not from raw tags. Skipping step 2 leaves it stale.

## Commits

- Primary author **must** be Sergey: every `git commit` needs
  `--author="Sergey Bulaev <s@bulaev.org>"`. The harness defaults to the Claude
  identity if you forget; verify with `git log -1 --format='%an <%ae>'` before
  pushing.
- Co-author trailer (`Co-Authored-By: Claude ...`) is fine and welcomed.
- Verify locally before push: build never breaks, no broken refs in `SKILL.md`,
  library smoke import passes.

## Skill bundle invariants

- **Exactly 8 skills.** Adding requires merging or splitting elsewhere to stay at
  6. The number is announced in plugin manifests and the README.
- **Frontmatter `description:` target <= 400 chars** (some bundle-heavy skills
  land slightly higher when their scope is genuinely broad; keep under 510).
  Always include a "Not for X (use Y)" disambiguation sentinel when a skill
  overlaps with a sibling.
- **No em dashes anywhere in `description:` fields.** Em dashes in body prose are
  allowed for table separators and list dividers only. No em dashes inside the
  literal fill-in lines of any hook skeleton (they would leak into generated
  tweets).
- **Skill names are public surface.** Renaming a skill is a major version bump and
  requires updating: `.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json`, `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, root `SKILL.md` bundle list, README skill
  table, and every `x-<name>` cross-reference in sibling SKILL.md files.

## Voice rules + reference layout

- Canonical voice rules live at root `references/voice-rules.md`. Skill-local
  "Hard rules" sections must only contain skill-specific overrides (char ranges,
  thread rules, format constraints) and start with: `Global voice rules: see root
  SKILL.md Voice rules.`
- Other root-level references shared across skills:
  `references/hook-formulas.md` (10 X formulas) and
  `references/algorithm-heuristics.md`.
- Skill-local references live in `skills/<skill>/references/`. Cite from the skill
  with bare `references/X.md`. Cite root from skills with `../../references/X.md`.
- `x-humanizer` has `sub-skills/` for the folded-in post-audit workflow. Don't
  duplicate this pattern in other skills without a clear reason.

## Layer separation

- **Write layer (Publora):** `lib/publora_client.py`. Two methods used by the
  bundle: `create_post` (single tweet or thread; pass long content and Publora
  auto-splits into a numbered `(1/N)` thread) and `list_connections` /
  `x_connections` (GET /platform-connections). Skills should call
  `lib.publish(kind, draft_text, target_url, ...)` rather than inline the
  publora / manual / diy dispatch. Real endpoint: `POST /create-post` with
  `platforms: ["twitter-<id>"]` (an array of STRING ids), header `x-publora-key`.
- **X has no comment/reply/reaction endpoint on Publora** (those are LinkedIn
  only), and `create-post` has no `in_reply_to`. So `kind="reply"` always routes
  to a manual copy-paste block in `lib/backend_selector.py`.
- **No read layer ships by default.** There is no cheap, documented X tweet-read
  actor wired in. `x-hook-extractor` and `x-reply-drafter` ask the user to paste
  the tweet text. If a tweet-read actor is added later, gate it behind
  `APIFY_TOKEN` and keep the paste fallback.
- Don't name competing third-party schedulers in committed files. The bundle is
  positioned around the Publora write integration.

## Codex marketplace package

- Codex requires marketplace entries to point at a nested plugin directory. The
  root remains the Claude-facing source layout.
- `.agents/plugins/marketplace.json` points to `.codex-marketplace/x-skills`.
- `scripts/sync_codex_marketplace.py` copies the root Codex manifest, `SKILL.md`,
  `skills/`, `references/`, `lib/`, `scripts/`, `requirements.txt`, `.env.example`,
  and `LICENSE` into the hidden package.
- After editing any copied file, run the sync script before testing or committing.

## testing/ is gitignored

- `testing/` is the local scratch directory: API keys, sample API responses,
  validation reports, integration scripts.
- Never write secrets above `testing/` (the rest of the repo is public).
- The `.gitignore` rule for `testing/` is load-bearing; do not change it.

## Validation before push

Run from repo root:

```bash
python3 -c "from lib import publish, parse_x_url, PubloraClient; print('OK')"
python3 scripts/sync_codex_marketplace.py
ls skills/ | wc -l        # must equal 8
grep -rnP '\x{2014}|\x{2013}' skills/*/SKILL.md SKILL.md | grep -i '^.*description:'   # must be empty
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
```

If any of these fail, do not push.
