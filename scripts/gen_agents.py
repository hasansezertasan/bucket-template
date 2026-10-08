#!/usr/bin/env python3
"""Regenerate agent instructions and skills from ``.ai-rulez/``.

``.ai-rulez/`` is the single source; ``ai-rulez generate`` renders it into
``AGENTS.md``, ``.claude/skills/``, and ``.agents/skills/``. Those outputs are
committed (``.gitignore`` is Cobo-managed), so this wrapper keeps them
reproducible:

- It deletes the side files the presets always write, since ai-rulez offers no
  switch to turn them off. ``CLAUDE.md`` and ``GEMINI.md`` would duplicate
  ``AGENTS.md``, which Claude Code and Antigravity read. ``.agents/settings.json``
  registers an MCP server launched with ``npx -y ai-rulez@latest``, an unpinned
  package an agent would run at session start.
- ``--check`` renders into a temporary copy and compares it with the working
  tree, so a stale or hand-edited output fails without the check modifying any
  file. Existing outputs are seeded into the copy first: ai-rulez skips files
  whose content is unchanged, which keeps their ``Generated:`` timestamp stable.

Standard library only; requires the ``ai-rulez`` binary from ``mise install``.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = ".ai-rulez"
MANIFEST = f"{CONFIG_DIR}/.generated-manifest.json"
DROPPED = ("CLAUDE.md", "GEMINI.md", ".agents/settings.json")
# Directories owned entirely by generation; any other file in them is stale.
# Only skills/ under .claude/, since .claude/ also holds local user settings.
OWNED_DIRS = (".claude/skills", ".agents")
# Seeded into the temporary copy so unchanged outputs keep their timestamps.
SEED = ("AGENTS.md", ".claude/skills", ".agents")


def run_ai_rulez(root: Path) -> None:
    """Run ``ai-rulez generate`` for the config under ``root`` and post-process."""
    binary = shutil.which("ai-rulez")
    if binary is None:
        sys.exit("ai-rulez not found on PATH; run `mise install` first.")
    config = root / CONFIG_DIR / "config.yaml"
    subprocess.run(
        [binary, "generate", "--quiet", "--no-configure-cli-mcp", "--config", str(config)],
        cwd=root,
        check=True,
    )
    drop_unwanted(root)


def drop_unwanted(root: Path) -> None:
    """Delete the unwanted outputs and remove them from the generation manifest."""
    for rel in DROPPED:
        (root / rel).unlink(missing_ok=True)
    manifest = root / MANIFEST
    if not manifest.is_file():
        return
    data = json.loads(manifest.read_text(encoding="utf-8"))
    files = data.get("files", [])
    kept = [f for f in files if f not in DROPPED]
    if kept != files:
        data["files"] = kept
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def expected_files(root: Path) -> set[str]:
    """Return every output path recorded in ``root``'s manifest, plus the manifest."""
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    return {*data.get("files", []), MANIFEST}


def owned_files(root: Path) -> set[str]:
    """Return every file currently present under the generation-owned directories."""
    found = set()
    for owned in OWNED_DIRS:
        base = root / owned
        if base.is_dir():
            found.update(p.relative_to(root).as_posix() for p in base.rglob("*") if p.is_file())
    return found


def compare(rendered: Path, repo: Path) -> list[str]:
    """Describe how ``repo``'s outputs differ from a fresh render in ``rendered``."""
    expected = expected_files(rendered)
    problems = []
    for rel in sorted(expected):
        target = repo / rel
        if not target.is_file():
            problems.append(f"missing: {rel}")
        elif not filecmp.cmp(rendered / rel, target, shallow=False):
            problems.append(f"stale: {rel}")
    problems.extend(f"not generated: {rel}" for rel in sorted(owned_files(repo) - expected))
    return problems


def check() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copytree(REPO / CONFIG_DIR, work / CONFIG_DIR)
        for rel in SEED:
            source = REPO / rel
            if source.is_dir():
                shutil.copytree(source, work / rel)
            elif source.is_file():
                shutil.copy2(source, work / rel)
        run_ai_rulez(work)
        problems = compare(work, REPO)
    if problems:
        print("Generated agent files are out of date with .ai-rulez/:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("Run `mise run agents:generate` and commit the result.", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated files differ from .ai-rulez/, without writing them",
    )
    args = parser.parse_args(argv)
    if args.check:
        return check()
    run_ai_rulez(REPO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
