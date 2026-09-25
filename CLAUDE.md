# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude skill (`linkedin-job-outreach`), not an application. `SKILL.md` is the entry point: its frontmatter `description` controls when the skill triggers, and its body defines the workflow Claude follows when searching LinkedIn via Claude in Chrome, triaging job posts/alerts, drafting recruiter messages and sending the approved ones, driven by the user's own profile. All skill content is written in Portuguese; keep it that way when editing.

## Structure and how the pieces connect

- `SKILL.md` — workflow: search posts in Chrome → load profile → check duplicates via tracker → apply red flags → score fit (0–10) → pick channel (DM / invite / comment) and draft messages for score ≥ 6 → user approves by ID → send approved ones one by one, registering each in the tracker. Also defines the approval-list format.
- `references/profile.template.md` — generic template for the candidate profile (stack, eliminatory conditions, search terms, daily cap, scoring rubric). The real profile is **not** in the repo: it lives at `~/.linkedin-job-outreach/profile.md` (override: `JOB_OUTREACH_PROFILE`) so plugin updates don't overwrite it and personal data isn't published. `tracker.py profile` creates it from the template and reports `CRIADO`/`INCOMPLETO`/`OK` (incomplete = the `<!-- TEMPLATE` marker is still there); `SKILL.md` runs guided setup on the first two. Keep candidate-specific data out of every file in the repo.
- `references/red-flags.md` — "grave" flags discard the job with no message; "moderada" flags are kept but noted in the Fit field.
- `references/messages.md` — message rules (DM ~500 chars, invite note ≤ 200 chars, language matches the post) plus examples and follow-up guidance.
- `scripts/tracker.py` — stdlib-only SQLite CLI tracking recruiter contacts. DB defaults to `~/.linkedin-job-outreach/tracker.db`; override with env var `JOB_OUTREACH_DB` (use this for testing so the real DB isn't touched).

- `skills/follow-up/SKILL.md` — second skill (`/linkedin-job-outreach:follow-up`): scans LinkedIn DMs, classifies job conversations, drafts follow-ups matching each chat's language/tone. It reuses the root skill's send rules and reaches shared files via `${CLAUDE_SKILL_DIR}/../../`. The root `SKILL.md` also points to it, so it works when the repo is cloned as a standalone skill (where nested skills aren't discovered).
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — the repo is both a plugin (root `SKILL.md` loads via `"skills": ["./"]`, alongside `skills/`) and a marketplace (`renanmachad-plugins`, plugin `source: "./"`). Bump `version` in `plugin.json` on every release, otherwise installed users stay on the old version. Validate with `claude plugin validate .`.

In `SKILL.md`, always reference bundled files as `${CLAUDE_SKILL_DIR}/...` (e.g. `python "${CLAUDE_SKILL_DIR}/scripts/tracker.py"`): the skill runs from the user's project directory, so bare relative paths break once installed.

If you rename a tracker subcommand, flag, `--channel` choice (`dm|comment|invite|email`) or status (`sent|replied|interview|rejected|ghosted`), update the invocations in `SKILL.md` to match.

## Tracker commands

Use `python`, not `python3` — on this Windows machine `python3` resolves to the Microsoft Store stub.

```bash
python scripts/tracker.py check --name "<recrutador>" --company "<empresa>" [--url ...] [--days 30]
python scripts/tracker.py add --name ... --company ... --role ... --url ... --channel dm --score 8 [--notes ...]
python scripts/tracker.py list [--status sent] [--older-than 7]
python scripts/tracker.py update --id <id> --status replied [--notes ...]
python scripts/tracker.py stats
python scripts/tracker.py today [--limit 10]   # daily outreach cap check before sending
python scripts/tracker.py profile               # path + status of the local profile
```

`check` and `profile` print a status token on its first line (`NOVO`, `JA_CONTATADO_RECENTE`, `CONTATADO_ANTES`, `RECRUTADOR_NOVO_EMPRESA_JA_CONTATADA`) that the skill workflow branches on — preserve these strings.

There are no tests, build, or lint setup. To exercise the script safely:

```bash
JOB_OUTREACH_DB=/tmp/test.db JOB_OUTREACH_PROFILE=/tmp/profile.md python scripts/tracker.py profile
```

## Non-negotiable constraints

LinkedIn prohibits automation, so account restriction is the main risk. The rules in `SKILL.md` ("Regras inegociáveis") must survive any edit:
- Browsing, searching and reading are autonomous; every send (DM, invite, comment, follow-up) requires the user's explicit approval of that specific message in chat.
- Daily cap (default 10) enforced via `tracker.py today`; stop immediately on CAPTCHA/security checks/login walls — never bypass them.
- Only the user's real browser via Claude in Chrome — no console scripts, Playwright/Puppeteer, or direct API calls.
