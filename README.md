# Antigravity IDE x Claude — Full Setup Guide

> **AG** = Antigravity IDE, **CC** = Claude Code throughout this guide.

Use Claude Sonnet / Opus 4.6 inside [Antigravity IDE](https://antigravity.dev). Gemini Pro subscribers get a free Claude credit allowance each month. No separate Anthropic subscription required to get started.

---

## What this guide covers

- Switch Antigravity IDE from Gemini to Claude
- Set up `GEMINI.md` as a persistent system prompt (equivalent to Claude Code's `CLAUDE.md`)
- Add security rules that compensate for Antigravity's lack of hook-level blocking
- *(Optional)* Bidirectional memory sync if you also use Claude Code
- *(Optional)* Skill / slash command sync if you also use Claude Code

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Gemini Pro subscription** | For bundled Claude credits; skip if using your own Anthropic API key |
| **Antigravity IDE** | Download at [antigravity.dev](https://antigravity.dev) |
| **Python 3.9+** | Only needed for the memory/skill sync scripts |
| **Claude Code** | Optional — only for the CC↔AG sync sections |

---

## Part 1 — Switch to Claude and set up your workspace

### 1.1 Select Claude model in Antigravity IDE

Open Antigravity IDE, then in the model selector choose **Claude Sonnet 4.6** or **Claude Opus 4.6**.

Your Gemini Pro subscription includes a monthly Claude credit allowance. Once you exhaust it, you can add your own Anthropic API key in Settings → API Keys.

### 1.2 Set up `GEMINI.md` as your system prompt

Antigravity IDE reads `GEMINI.md` from the workspace root at the start of every conversation. This file acts as a persistent system prompt — everything you put here applies to every session automatically.

Copy the starter template from this repo:

```bash
cp templates/GEMINI.md /path/to/your/workspace/GEMINI.md
```

Then edit it to add your own project rules, coding standards, or any context you want the model to carry across sessions.

### 1.3 Add security rules to `GEMINI.md`

Claude Code enforces security at the OS level via shell hooks. Antigravity IDE has no equivalent hook mechanism — only soft rules via `GEMINI.md`. Add the block below to your `GEMINI.md`:

```markdown
## Security Rules

Never read, print, inspect, or pass to any tool the contents of:
- `~/.clasprc.json` and any `~/.clasprc*.json`
- `.env`, `.env.*` (any environment variable file)
- Any file named `credentials.json` or `service-account.json`
- Any file whose name contains `secret`, `token`, `key`, or `credential`

Before running `git push`, verify the staged diff does not contain:
- API key patterns: `sk-ant-`, `sk-proj-`, `AIza`, `ghp_`, `github_pat_`, `-----BEGIN PRIVATE KEY`
- Any of the sensitive filenames listed above

If you detect a violation, stop immediately and ask the user to confirm before proceeding.
```

> **Important:** These are AI-enforced soft rules. Unlike Claude Code hooks (which block at the system call level), the model may occasionally miss edge cases. For operations involving sensitive credentials, Claude Code provides stronger guarantees.

---

## Part 2 — Sync with Claude Code (optional)

Skip this section if you use Antigravity IDE standalone, without Claude Code.

### 2.1 Sync system prompt (symlink)

If you already have a `CLAUDE.md` in your workspace, create a symlink instead of maintaining two separate files:

```bash
ln -s /path/to/your/workspace/CLAUDE.md /path/to/your/workspace/GEMINI.md
```

After this, every edit to `CLAUDE.md` takes effect in AG immediately. Single source of truth.

To verify the symlink:
```bash
ls -la /path/to/your/workspace/GEMINI.md
# Should show: GEMINI.md -> /path/to/your/workspace/CLAUDE.md
```

### 2.2 Sync memory (CC to AG and back)

Claude Code stores memory as `.md` files with YAML frontmatter in:
```
~/.claude/projects/<project-hash>/memory/
```

Antigravity IDE stores memory as "Knowledge Items (KI)" in:
```
~/.gemini/antigravity-ide/knowledge/<ki-name>/
```

The formats are incompatible — `scripts/memory_sync.py` converts between them.

#### Setup

**Step 1** — Find your Claude Code project hash:

```bash
ls ~/.claude/projects/
```

The directory name is your workspace path with `/` replaced by `-`. For example, `/Users/alice/my-project` becomes `-Users-alice-my-project`.

**Step 2** — Edit the CONFIG section at the top of `scripts/memory_sync.py`:

```python
# === CONFIG ===
CC_MEMORY_DIR = Path.home() / ".claude" / "projects" / "YOUR-PROJECT-HASH" / "memory"
AG_KI_DIR     = Path.home() / ".gemini" / "antigravity-ide" / "knowledge"
```

**Step 3** — Run a test sync:

```bash
python3 scripts/memory_sync.py
```

**Step 4** — Set up automatic sync via launchd (macOS):

```bash
# Edit the template — replace YOUR-USERNAME and path placeholders
cp scripts/com.username.memory-sync.plist.template \
   ~/Library/LaunchAgents/com.YOUR-USERNAME.memory-sync.plist

# Edit the plist to fill in your actual paths, then load it:
launchctl load ~/Library/LaunchAgents/com.YOUR-USERNAME.memory-sync.plist
```

The default interval is every 5 minutes. Adjust `StartInterval` in the plist to change it.

#### How sync loops are prevented

Every memory synced from CC to AG gets a `claude-memory-` prefix in its KI name. The AG→CC direction only processes KIs without that prefix, so CC memories never get re-synced back.

#### Useful commands

```bash
# Check sync status
launchctl list | grep memory-sync

# View recent sync log
tail -50 ~/.gemini/antigravity-ide/sync_memory_to_ki.log

# Force a manual sync
python3 scripts/memory_sync.py

# Stop auto-sync
launchctl unload ~/Library/LaunchAgents/com.YOUR-USERNAME.memory-sync.plist
```

### 2.3 Sync skills / slash commands

Claude Code reads slash commands from `~/.claude/commands/`.  
Antigravity IDE reads skills from `~/.gemini/config/plugins/<plugin-name>/skills/`.

`scripts/skill_sync_setup.py` creates symlinks so both IDEs read the same source files — no duplication, no drift.

#### Requirement: YAML frontmatter

Each skill `.md` file needs a frontmatter header. Antigravity IDE reads this to register the skill name and description:

```markdown
---
name: my-skill
description: One line describing what this skill does
---

(skill content starts here)
```

Claude Code also reads this frontmatter but does not require it.

#### Setup

**Step 1** — Edit the CONFIG section at the top of `scripts/skill_sync_setup.py`:

```python
# === CONFIG ===
SKILL_DIR  = Path("/path/to/your/skills/folder")
PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "personal-skills"
```

**Step 2** — Add frontmatter to any skill files that are missing it, then run:

```bash
python3 scripts/skill_sync_setup.py
```

The script is idempotent — safe to re-run whenever you add a new skill. No need to restart Antigravity IDE; new skills take effect immediately.

---

## What MCP tools carry over?

MCP server configuration lives separately from the sync covered above. Behavior by MCP type:

| MCP type | Works in AG? | How |
|---|---|---|
| API key-based (e.g. Perplexity Search) | Yes | Add the same config and key to `~/.gemini/config/mcp_config.json` |
| OAuth-based (Gmail, Calendar, Drive) | Yes, separately | Each IDE needs its own OAuth flow — tokens are stored per application |
| Claude.ai remote MCPs (`mcp__claude_ai_*`) | No | AG has no claude.ai auth layer; use `gws-*` Google Workspace MCPs instead |

---

## Limitations vs Claude Code

| Feature | Claude Code | Antigravity IDE |
|---|---|---|
| System prompt | `CLAUDE.md` | `GEMINI.md` |
| Persistent memory | Native | Synced via script (5 min lag) |
| Slash commands / skills | Native | Synced via symlinks |
| Hook-level security blocks | Hard block (OS level) | Soft rules only (GEMINI.md) |
| Auto clasp push for `.gs` files | Automatic via hook | Manual — run `clasp push` yourself |
| Python QA auto-run | Automatic via hook | Not available |
| MCP: API key servers | Full support | Requires manual config |
| MCP: OAuth servers | Full support | Separate OAuth flow required |

---

## Claude quota in Antigravity IDE — set your expectations

Gemini Pro includes a Claude credit allowance in Antigravity IDE. Before you get excited: the actual quota is small.

Based on real usage (as of 2026-06-18):

- Each 5-hour Claude session in AG is roughly **3% of what a Claude Pro subscriber gets in Claude Code**
- Antigravity IDE gives you **3 of these sessions per week**
- That means AG's weekly Claude budget is around **10% of a single Claude Code 5-hour window**

**Who this setup is actually useful for:**

1. **Gemini Pro subscribers who don't pay for Claude Pro** — you get some Claude access at no extra cost, and with this setup it behaves like a proper Claude Code environment (memory, skills, system prompt all carry over)

2. **Claude Code users who hit their quota** — when your CC session runs out mid-task, AG gives you a small buffer to wrap up loose ends without switching mental context

If you need full Claude capacity, adding your own Anthropic API key to AG's settings bypasses the bundled quota and bills at standard API pricing.

---

## Battle-tested

Setup approach adapted from a real CC + AG dual-environment with:
- 21 personal skills synced
- 138 memory items bidirectionally synced
- Launchd auto-sync running in production since 2026-06-18
