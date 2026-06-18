#!/usr/bin/env python3
"""
memory_sync.py
Bidirectional sync: Claude Code memory <-> Antigravity IDE Knowledge Items (KI)

Direction A (CC -> AG):
  Source: ~/.claude/projects/<project-hash>/memory/*.md
  Target: ~/.gemini/antigravity-ide/knowledge/claude-memory-<slug>/

Direction B (AG -> CC):
  Source: ~/.gemini/antigravity-ide/knowledge/<non-prefixed KI>/
  Target: ~/.claude/projects/<project-hash>/memory/<slug>.md

Loop prevention:
  CC-originated KIs get a "claude-memory-" prefix.
  The AG->CC direction only processes KIs without that prefix,
  so CC memories are never re-synced back.
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# =============================================================================
# CONFIG — edit these two paths before running
# =============================================================================
#
# CC_MEMORY_DIR: find your project hash with: ls ~/.claude/projects/
#   The directory name is your workspace path with "/" replaced by "-".
#   Example: /Users/alice/my-project -> -Users-alice-my-project
#
CC_MEMORY_DIR = Path.home() / ".claude" / "projects" / "YOUR-PROJECT-HASH" / "memory"

#
# AG_KI_DIR: standard Antigravity IDE path, no need to change unless you
#   installed AG in a non-default location.
#
AG_KI_DIR = Path.home() / ".gemini" / "antigravity-ide" / "knowledge"

# =============================================================================

KI_PREFIX  = "claude-memory-"   # CC -> AG KI prefix (loop prevention)
SKIP_FILES = {"MEMORY.md"}      # skip index file if present


# ── Utilities ─────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter. Returns (meta_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_fm = parts[1].strip()
    body   = parts[2].strip()
    meta   = {}
    for line in raw_fm.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if k and not k.startswith(" "):
                meta[k] = v
    return meta, body


def build_summary(meta: dict, body: str, slug: str) -> str:
    """Build a summary string for the KI metadata."""
    name = meta.get("name") or slug
    desc = meta.get("description") or ""
    first_line = next(
        (l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")),
        ""
    )
    if desc:
        return f"{name}: {desc}"
    elif first_line:
        return f"{name}: {first_line[:120]}"
    return name


# ── Direction A: CC -> AG ──────────────────────────────────────────────────────

def sync_cc_to_ag(md_path: Path) -> str:
    """Sync one Claude memory file to a KI. Returns 'created' / 'updated' / 'skipped'."""
    slug    = md_path.stem
    ki_dir  = AG_KI_DIR / f"{KI_PREFIX}{slug}"
    meta_f  = ki_dir / "metadata.json"
    art_dir = ki_dir / "artifacts"
    art_f   = art_dir / md_path.name

    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    # mtime check: skip if KI is newer than source
    if meta_f.exists() and art_f.exists():
        if meta_f.stat().st_mtime >= md_path.stat().st_mtime:
            return "skipped"
        status = "updated"
    else:
        status = "created"

    ki_dir.mkdir(parents=True, exist_ok=True)
    art_dir.mkdir(parents=True, exist_ok=True)
    art_f.write_text(text, encoding="utf-8")

    now_iso = datetime.now(timezone.utc).isoformat()
    metadata = {
        "summary": build_summary(meta, body, slug),
        "created_at": now_iso,
        "updated_at": now_iso,
        "type": meta.get("type", "other"),
        "source": "claude-memory-sync",
        "references": [
            {"type": "file", "path": str(md_path), "description": f"Claude Code memory source: {slug}"}
        ],
        "artifacts": [str(art_f)]
    }
    meta_f.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


def remove_stale_cc_ki(memory_slugs: set) -> list:
    """Delete claude-memory-* KIs that no longer exist in CC memory."""
    removed = []
    if not AG_KI_DIR.exists():
        return removed
    for ki_dir in AG_KI_DIR.iterdir():
        if not ki_dir.is_dir() or not ki_dir.name.startswith(KI_PREFIX):
            continue
        slug = ki_dir.name[len(KI_PREFIX):]
        if slug not in memory_slugs:
            shutil.rmtree(ki_dir)
            removed.append(slug)
    return removed


def run_cc_to_ag() -> dict:
    """Run CC -> AG sync. Returns counts."""
    if not CC_MEMORY_DIR.exists():
        print(f"[ERROR] CC memory directory not found: {CC_MEMORY_DIR}", file=sys.stderr)
        print("        Check your CC_MEMORY_DIR setting in the CONFIG section.", file=sys.stderr)
        return {}

    AG_KI_DIR.mkdir(parents=True, exist_ok=True)
    md_files = [f for f in CC_MEMORY_DIR.glob("*.md") if f.name not in SKIP_FILES]
    memory_slugs = {f.stem for f in md_files}

    counts = {"created": 0, "updated": 0, "skipped": 0}
    for md_path in sorted(md_files):
        result = sync_cc_to_ag(md_path)
        counts[result] += 1
        if result != "skipped":
            print(f"  [CC->AG {result:7s}] {md_path.name}")

    removed = remove_stale_cc_ki(memory_slugs)
    for slug in removed:
        print(f"  [CC->AG removed ] {slug}")

    print(
        f"\nCC->AG: {counts['created']} created, {counts['updated']} updated, "
        f"{counts['skipped']} skipped, {len(removed)} removed "
        f"(total {len(md_files)} files)"
    )
    return counts


# ── Direction B: AG -> CC ──────────────────────────────────────────────────────

def ki_to_memory_md(ki_dir: Path) -> str:
    """Convert a KI (metadata.json + artifacts) to Claude memory markdown format."""
    meta_f = ki_dir / "metadata.json"
    if not meta_f.exists():
        return ""

    meta    = json.loads(meta_f.read_text(encoding="utf-8"))
    summary = meta.get("summary", ki_dir.name)
    ki_type = meta.get("type", "other")
    created = meta.get("created_at", "")
    source  = meta.get("source", "antigravity")

    art_dir = ki_dir / "artifacts"
    body_parts = []
    if art_dir.exists():
        for art_f in sorted(art_dir.glob("*.md")):
            content = art_f.read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)
            body_parts.append(body if body else content)

    body = "\n\n".join(body_parts) if body_parts else "*(no artifact content)*"

    fm = (
        f"---\n"
        f"name: {ki_dir.name}\n"
        f"description: {summary}\n"
        f"metadata:\n"
        f"  node_type: memory\n"
        f"  type: {ki_type}\n"
        f"  source: {source}\n"
        f"  synced_from_ag: true\n"
        f"  original_created: {created}\n"
        f"---"
    )
    return f"{fm}\n\n{body}\n"


def sync_ag_to_cc(ki_dir: Path) -> str:
    """Sync one AG KI to CC memory. Returns 'created' / 'updated' / 'skipped'."""
    slug   = ki_dir.name
    dest_f = CC_MEMORY_DIR / f"{slug}.md"
    meta_f = ki_dir / "metadata.json"

    if not meta_f.exists():
        return "skipped"

    if dest_f.exists():
        if dest_f.stat().st_mtime >= meta_f.stat().st_mtime:
            return "skipped"
        status = "updated"
    else:
        status = "created"

    content = ki_to_memory_md(ki_dir)
    if not content:
        return "skipped"

    dest_f.write_text(content, encoding="utf-8")
    return status


def remove_stale_ag_memory(ag_slugs: set) -> list:
    """Delete CC memory files that were synced from AG but no longer exist in AG."""
    removed = []
    if not CC_MEMORY_DIR.exists():
        return removed
    for md_f in CC_MEMORY_DIR.glob("*.md"):
        if md_f.name in SKIP_FILES:
            continue
        try:
            text = md_f.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter(text)
            if meta.get("synced_from_ag") != "true":
                continue
        except Exception:
            continue
        if md_f.stem not in ag_slugs:
            md_f.unlink()
            removed.append(md_f.stem)
    return removed


def run_ag_to_cc() -> dict:
    """Run AG -> CC sync. Returns counts."""
    if not AG_KI_DIR.exists():
        print("[SKIP] AG knowledge directory not found — nothing to sync AG->CC")
        return {}

    CC_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    # Only process KIs without the CC prefix (native AG-created KIs)
    native_ki_dirs = [
        d for d in AG_KI_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(KI_PREFIX)
    ]
    ag_slugs = {d.name for d in native_ki_dirs}

    counts = {"created": 0, "updated": 0, "skipped": 0}
    for ki_dir in sorted(native_ki_dirs):
        result = sync_ag_to_cc(ki_dir)
        counts[result] += 1
        if result != "skipped":
            print(f"  [AG->CC {result:7s}] {ki_dir.name}")

    removed = remove_stale_ag_memory(ag_slugs)
    for slug in removed:
        print(f"  [AG->CC removed ] {slug}")

    print(
        f"\nAG->CC: {counts['created']} created, {counts['updated']} updated, "
        f"{counts['skipped']} skipped, {len(removed)} removed "
        f"(total {len(native_ki_dirs)} native KIs)"
    )
    return counts


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print(f"Sync started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    print("\n[CC -> AG]")
    run_cc_to_ag()

    print("\n[AG -> CC]")
    run_ag_to_cc()

    print("\nDone.")


if __name__ == "__main__":
    main()
