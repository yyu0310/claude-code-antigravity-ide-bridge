#!/usr/bin/env python3
"""
skill_sync_setup.py
Create an Antigravity IDE plugin that symlinks to your existing skill files,
so Claude Code and Antigravity IDE share the same skill source — no duplication.

Run once for setup. Re-run whenever you add a new skill. Idempotent.

Steps:
  1. Warn about any skill files missing YAML frontmatter (you must add it manually)
  2. Create ~/.gemini/config/plugins/personal-skills/ plugin structure
  3. Create a symlink for each skill: <plugin>/skills/<name>/SKILL.md -> SKILL/<name>.md

Frontmatter format required by Antigravity IDE:
  ---
  name: my-skill
  description: One line describing what this skill does
  ---
  (skill content)
"""

import json
import sys
from pathlib import Path

# =============================================================================
# CONFIG — edit these paths before running
# =============================================================================
#
# SKILL_DIR: folder containing your .md skill files
#   Each file should be named <skill-name>.md
#
SKILL_DIR = Path("/path/to/your/skills/folder")

#
# PLUGIN_DIR: where to create the AG plugin. Standard path — change only if
#   you installed Antigravity in a non-default location.
#
PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "personal-skills"

#
# SKIP_FILES: filenames to ignore in SKILL_DIR (index files, READMEs, etc.)
#
SKIP_FILES = {"_index.md", "README.md"}

# =============================================================================


def check_frontmatter(skill_file: Path) -> bool:
    """Return True if file has YAML frontmatter."""
    text = skill_file.read_text(encoding="utf-8")
    return text.startswith("---")


def setup_plugin() -> Path:
    """Create the personal-skills plugin structure. Returns the skills/ directory."""
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    plugin_json = {
        "name": "personal-skills",
        "version": "1.0.0",
        "description": "Personal workflow skills synced from a shared source folder",
        "author": {"name": "you"}
    }
    plugin_f = PLUGIN_DIR / "plugin.json"
    plugin_f.write_text(json.dumps(plugin_json, ensure_ascii=False, indent=2), encoding="utf-8")
    skills_dir = PLUGIN_DIR / "skills"
    skills_dir.mkdir(exist_ok=True)
    return skills_dir


def create_skill_symlink(skills_dir: Path, slug: str, source_file: Path) -> str:
    """Create <slug>/SKILL.md symlink pointing to source_file."""
    skill_dir = skills_dir / slug
    skill_dir.mkdir(exist_ok=True)
    symlink = skill_dir / "SKILL.md"

    if symlink.is_symlink():
        if symlink.resolve() == source_file.resolve():
            return "exists"
        symlink.unlink()  # wrong target — rebuild

    symlink.symlink_to(source_file)
    return "created"


def main():
    if not SKILL_DIR.exists():
        print(f"[ERROR] SKILL_DIR not found: {SKILL_DIR}", file=sys.stderr)
        print("        Check your SKILL_DIR setting in the CONFIG section.", file=sys.stderr)
        sys.exit(1)

    skill_files = sorted(f for f in SKILL_DIR.glob("*.md") if f.name not in SKIP_FILES)
    print(f"Found {len(skill_files)} skill files\n")

    # Step 1: Check frontmatter
    print("[Step 1] Checking YAML frontmatter")
    ready = []
    for skill_file in skill_files:
        slug = skill_file.stem
        if check_frontmatter(skill_file):
            print(f"  [ok     ] {skill_file.name}")
            ready.append(skill_file)
        else:
            print(f"  [MISSING] {skill_file.name} — add frontmatter manually before re-running:")
            print(f"            ---")
            print(f"            name: {slug}")
            print(f"            description: One line describing what this skill does")
            print(f"            ---")

    if not ready:
        print("\nNo skills with frontmatter found. Add frontmatter and re-run.")
        sys.exit(0)

    # Step 2: Create plugin structure
    print(f"\n[Step 2] Creating plugin structure")
    skills_dir = setup_plugin()
    print(f"  plugin.json -> {PLUGIN_DIR}/plugin.json")
    print(f"  skills/     -> {skills_dir}")

    # Step 3: Create symlinks
    print(f"\n[Step 3] Creating symlinks")
    for skill_file in ready:
        slug = skill_file.stem
        result = create_skill_symlink(skills_dir, slug, skill_file)
        print(f"  [{result:7s}] {slug}/SKILL.md -> {skill_file.name}")

    print(f"\nDone. AG plugin path: {PLUGIN_DIR}")
    print("Skills take effect immediately — no need to restart Antigravity IDE.")


if __name__ == "__main__":
    main()
