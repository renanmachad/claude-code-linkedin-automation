# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude skill (`linkedin-job-outreach`), not an application. `SKILL.md` is the entry point: its frontmatter `description` controls when the skill triggers, and its body defines the workflow Claude follows when searching LinkedIn via Claude in Chrome, triaging job posts/alerts, drafting recruiter messages and sending the approved ones, driven by the user's own profile and CV memory. Three more skills live under `skills/` (follow-up, cv, candidatura); the repo is packaged as a Claude Code plugin + marketplace. All skill content is written in Portuguese; keep it that way when editing.

## Structure and how the pieces connect

- `SKILL.md` — workflow: load profile and CV memory → search posts in Chrome → check duplicates via tracker → apply red flags → score fit (0–10) → pick channel (DM / invite / comment) and draft messages for score ≥ 6 → for posts with an apply link, pre-map the form read-only (up to 5) and include the fill plan → user approves by ID in one reply ("manda 1, candidata 2") → send/apply one by one, registering each in the tracker. Also defines the approval-list format.
- `references/profile.template.md` — generic template for the candidate profile (stack, eliminatory conditions, search terms, daily cap, scoring rubric). The real profile is **not** in the repo: it lives at `~/.linkedin-job-outreach/profile.md` (override: `JOB_OUTREACH_PROFILE`) so plugin updates don't overwrite it and personal data isn't published. `tracker.py profile` creates it from the template and reports `CRIADO`/`INCOMPLETO`/`OK` (incomplete = the `<!-- TEMPLATE` marker is still there); `SKILL.md` runs guided setup on the first two. Keep candidate-specific data out of every file in the repo.
- `references/red-flags.md` — "grave" flags discard the job with no message; "moderada" flags are kept but noted in the Fit field.
- `references/messages.md` — message rules (DM ~500 chars, invite note ≤ 200 chars, language matches the post, never conflate total years with domain years) plus fictitious examples and follow-up guidance.
- `scripts/tracker.py` — stdlib-only CLI: SQLite contact tracker plus helpers for the local profile, CV and application data. DB defaults to `~/.linkedin-job-outreach/tracker.db`; override with env var `JOB_OUTREACH_DB` (use this for testing so the real DB isn't touched).
- `skills/follow-up/SKILL.md` — second skill (`/linkedin-job-outreach:follow-up`): scans LinkedIn DMs, classifies job conversations, drafts follow-ups matching each chat's language/tone. It reuses the root skill's send rules and reaches shared files via `${CLAUDE_SKILL_DIR}/../../`. The root `SKILL.md` also points to it, so it works when the repo is cloned as a standalone skill (where nested skills aren't discovered).
- `skills/cv/SKILL.md` — third skill (`/linkedin-job-outreach:cv [path]`): `tracker.py cv --import` copies the CV (PDF/DOCX/MD/TXT) to `~/.linkedin-job-outreach/cv/` (override: `JOB_OUTREACH_CV_DIR`), `cv --text` extracts DOCX via stdlib zipfile (PDF is read by Claude directly), and Claude rewrites `cv/memoria.md` from scratch each run. The main and follow-up skills read that memory as an allowed source of facts for messages, alongside the profile.
- `skills/candidatura/SKILL.md` — fourth skill (`/linkedin-job-outreach:candidatura <url>`): fills job application forms on external sites via Claude in Chrome. Hard rules: only URLs the user gave or explicitly approved in chat; one approval per application of a complete field-by-field plan, which authorizes fill and submit of exactly that plan (several can be approved in one reply; any deviation stops before submit with a diff); account creation, login, passwords, verification codes, CAPTCHA and document numbers stay with the user. Form-only data (phone, salary, availability, work authorization) lives in `~/.linkedin-job-outreach/candidatura.md` from `references/candidatura.template.md` (`tracker.py candidatura`, override `JOB_OUTREACH_APPLICATION`); submissions are tracked with `--channel form`.
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — the repo is both a plugin (root `SKILL.md` loads via `"skills": ["./"]`, alongside `skills/`) and a marketplace (`renanmachad-plugins`, plugin `source: "./"`). Bump `version` in `plugin.json` on every release, otherwise installed users stay on the old version. Validate with `claude plugin validate .`.

In `SKILL.md`, always reference bundled files as `${CLAUDE_SKILL_DIR}/...` (e.g. `python "${CLAUDE_SKILL_DIR}/scripts/tracker.py"`): the skill runs from the user's project directory, so bare relative paths break once installed.

If you rename a tracker subcommand, flag, `--channel` choice (`dm|comment|invite|email|form`) or status (`sent|replied|interview|rejected|ghosted`), update the invocations in `SKILL.md` to match.

## Tracker commands

Skill files write `python`, and the root `SKILL.md` ("Interpretador Python") tells Claude to probe `python3 --version` once per session and use `python3` if it succeeds, else `python`: macOS/Linux often only have `python3`, while on Windows `python3` is a Microsoft Store stub that exits with code 49. When working in this repo on this Windows machine, use `python`.

```bash
python scripts/tracker.py check --name "<recrutador>" --company "<empresa>" [--url ...] [--days 30]
python scripts/tracker.py add --name ... --company ... --role ... --url ... --channel dm --score 8 [--notes ...]
python scripts/tracker.py list [--status sent] [--older-than 7]
python scripts/tracker.py update --id <id> --status replied [--notes ...]
python scripts/tracker.py stats
python scripts/tracker.py today [--limit 10]   # daily outreach cap check before sending
python scripts/tracker.py profile               # path + status of the local profile
python scripts/tracker.py candidatura           # path + status of the local application-form data
python scripts/tracker.py cv [--import PATH] [--text]   # import/show CV, memory path, extracted text
```

Several commands print a status token first that the skills branch on — preserve these strings:
- `check`: `NOVO`, `JA_CONTATADO_RECENTE`, `CONTATADO_ANTES`, `RECRUTADOR_NOVO_EMPRESA_JA_CONTATADA`
- `profile` / `candidatura`: `CRIADO`, `INCOMPLETO`, `OK`
- `cv`: `IMPORTADO`, `JA_IMPORTADO`, `SEM_CV`, `CV:`, `MEMORIA:` (`existe`/`ausente`), `PDF:`

There are no tests, build, or lint setup. To exercise the script safely:

```bash
JOB_OUTREACH_DB=/tmp/test.db JOB_OUTREACH_PROFILE=/tmp/profile.md JOB_OUTREACH_APPLICATION=/tmp/cand.md JOB_OUTREACH_CV_DIR=/tmp/cv python scripts/tracker.py profile
```

## Non-negotiable constraints

LinkedIn prohibits automation, so account restriction is the main risk. The rules in `SKILL.md` ("Regras inegociáveis") must survive any edit:
- Browsing, searching and reading are autonomous; every send (DM, invite, comment, follow-up) and every form submission requires the user's explicit approval of that specific message or fill plan in chat (one reply may approve several listed items).
- Daily cap (default 10) enforced via `tracker.py today`; stop immediately on CAPTCHA/security checks/login walls — never bypass them.
- Only the user's real browser via Claude in Chrome — no console scripts, Playwright/Puppeteer, or direct API calls.
