# Project Rules

<!--
  This file is read by Antigravity IDE at the start of every conversation.
  It acts as a persistent system prompt for your workspace.

  If you also use Claude Code, create a symlink instead of maintaining this file separately:
    ln -s /path/to/CLAUDE.md /path/to/GEMINI.md

  Customize the sections below for your project.
-->

## Security Rules

Never read, print, inspect, or pass to any tool the contents of:
- `~/.clasprc.json` and any `~/.clasprc*.json`
- `.env`, `.env.*` (any environment variable file)
- Any file named `credentials.json` or `service-account.json`
- Any file whose name contains `secret`, `token`, `key`, or `credential`

Before running `git push`, verify the staged diff does not contain:
- API key patterns: `sk-ant-`, `sk-proj-`, `AIza`, `ghp_`, `github_pat_`, `-----BEGIN PRIVATE KEY`
- Any of the sensitive filenames listed above

If you detect a violation, stop immediately and ask me to confirm before proceeding.

---

## Project Context

<!--
  Add context about what this project is and how it works.
  Example:
    This is a Python web app using FastAPI + PostgreSQL.
    Main entry point: src/main.py
    Run with: uvicorn src.main:app --reload
-->

---

## Coding Standards

<!--
  Add your preferred style, patterns, or constraints.
  Example:
    - Python: follow PEP 8, use type hints for all public functions
    - No print() in production code — use logging
    - Tests go in tests/, mirror the source structure
-->

---

## Behavior Preferences

<!--
  How you want the AI to work with you.
  Example:
    - Default to no comments in code unless the WHY is non-obvious
    - Prefer editing existing files over creating new ones
    - Ask before deleting any file
-->
