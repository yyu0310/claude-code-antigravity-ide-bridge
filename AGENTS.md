# AGENTS.md

This file provides context for AI assistants working in this repository.
In this repo, `CLAUDE.md` is a symlink pointing to this file — no content duplication. `GEMINI.md` is the template in `templates/` (not in the repo root).

---

## What this project is

A bridge setup for developers who use Claude Code in VS Code and want to extend the same AI environment to Antigravity IDE (Google's agent-first IDE).

The bridge covers four things:
1. **System prompt sync** — one `GEMINI.md` symlinked to `CLAUDE.md`, so both IDEs read the same rules
2. **Memory sync** — `scripts/memory_sync.py` converts between CC's `.md` format and AG's Knowledge Item (KI) folder format, runs every 5 minutes via launchd
3. **Skill sync** — `scripts/skill_sync_setup.py` creates symlinks so both IDEs read the same skill source files
4. **Security rules** — documented in `templates/GEMINI.md`, compensating for AG's lack of OS-level hook blocking

---

## Repository structure

```
README.md                                    Main guide (English)
README.zh-TW.md                              Traditional Chinese guide
README.zh-CN.md                              Simplified Chinese guide
AGENTS.md                                    This file (source of truth)
CLAUDE.md                                    Symlink → AGENTS.md (read by Claude Code)
llms.txt                                     LLM-friendly project summary
LICENSE                                      MIT
.gitignore
scripts/
  memory_sync.py                             CC ↔ AG memory sync script
  skill_sync_setup.py                        Skill symlink setup script
  com.username.memory-sync.plist.template    macOS launchd template
templates/
  GEMINI.md                                  Starter system prompt for AG
```

---

## Key design decisions

**Why not symlink memory?** CC memory is `.md` files with YAML frontmatter. AG memory (Knowledge Items) is a folder structure with `metadata.json` + `artifacts/`. Symlinks can't bridge format differences — a conversion script is the only option.

**Why symlink skills?** Skill files are plain `.md` with YAML frontmatter. Both IDEs read the same format, so a symlink is sufficient with zero lag and zero inconsistency.

**Loop prevention in memory sync:** CC-originated KIs get a `claude-memory-` prefix. The AG→CC direction only processes KIs without that prefix, preventing circular re-sync.

**Security rules are soft, not hard:** AG has no hook mechanism. The rules in `GEMINI.md` instruct the AI model, but cannot block at the OS level. Claude Code's hooks provide stronger guarantees.

---

## How to help a user with this project

Common tasks you may be asked to do:

- **Run memory sync**: `python3 scripts/memory_sync.py`
- **Add a new skill to AG**: user adds frontmatter to skill `.md`, then `python3 scripts/skill_sync_setup.py`
- **Check launchd status**: `launchctl list | grep memory-sync`
- **Add a new MCP server to AG**: edit `~/.gemini/config/mcp_config.json` — do NOT read this file if it contains API keys; use Edit directly
- **Find the CC project hash**: `ls ~/.claude/projects/` — directory name is workspace path with `/` replaced by `-`

---

## Security notes for AI assistants

- Do not read `~/.gemini/config/mcp_config.json` — it may contain API keys
- Do not read `.env` files or files named `credentials.json`, `service-account.json`
- Do not read files whose names contain `secret`, `token`, `key`, or `credential`
- Before any `git push`, confirm the diff contains no API key patterns (`sk-ant-`, `AIza`, `ghp_`, etc.)
