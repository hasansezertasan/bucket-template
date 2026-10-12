#!/usr/bin/env python3
"""Regenerate agent instructions and skills from ``.ai-rulez/``.

``.ai-rulez/`` is the single source; ``ai-rulez generate`` renders it into
``AGENTS.md``, ``.claude/skills/``, and ``.agents/skills/``. Those outputs are
committed (``.gitignore`` is Cobo-managed), so this wrapper keeps them
reproducible with a render-and-promote flow: ai-rulez owns rendering, the
wrapper owns packaging and drift checks.

- Render into a staging copy, so the side files the presets always write
  (``CLAUDE.md`` and ``GEMINI.md`` would duplicate ``AGENTS.md``, which Claude
  Code and Antigravity read) never touch the checkout. ai-rulez offers no
  switch to turn them off — native ``generate --check`` reports them as
  missing, which is why this wrapper keeps its own ``--check``.
- Promote (the default mode) copies the rendered files over and removes owned
  files the previous render produced but the fresh one no longer lists, so
  deleting a canonical skill removes its generated copies. Promotion refuses
  to write through symlinks and mirrors the owner-execute bit Git tracks.
  Dropped side files are neither promoted nor deleted by promote: a
  hand-written ``CLAUDE.md`` would shadow ``AGENTS.md`` for the agent that
  reads it, so ``--check`` reports it instead of vaporizing it. A previously
  generated file outside the owned sets is reported as orphaned rather than
  removed, since the maintainer may have adopted it by hand.
- ``--check`` renders into staging and compares it with the working tree, so a
  stale, missing, hand-edited, or unwanted output fails without modifying files.

Standard library only; requires the ``ai-rulez`` binary from ``mise install``.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = ".ai-rulez"
MANIFEST = f"{CONFIG_DIR}/.generated-manifest.json"
# Preset side files that must never reach the checkout: root duplicates of
# AGENTS.md. (ai-rulez stopped emitting .agents/settings.json under
# `[mcp] self_server = false` + `--no-self-mcp`; if it ever returns it rides
# the manifest like any other output instead of being silently dropped.)
DROPPED = ("CLAUDE.md", "GEMINI.md")
# Directories owned entirely by generation; any other file in them is stale.
# Only skills/ under .claude/, since .claude/ also holds local user settings.
OWNED_DIRS = (".claude/skills", ".agents")
# Root files only generation writes; one the config stops producing is stale.
OWNED_FILES = ("AGENTS.md",)


def find_binary() -> str:
    """Return the ``ai-rulez`` binary path or exit with a pointer to mise."""
    binary = shutil.which("ai-rulez")
    if binary is None:
        sys.exit("ai-rulez not found on PATH; run `mise install` first.")
    return binary


def render(source_root: Path, staging: Path) -> None:
    """Render ``source_root``'s config into ``staging`` and post-process it."""
    # v5 reads only config.toml (migrated from config.yaml); keep the yaml
    # fallback so the script still works on a pre-migration checkout.
    config = staging / CONFIG_DIR / "config.toml"
    shutil.copytree(source_root / CONFIG_DIR, staging / CONFIG_DIR)
    if not config.is_file():
        config = staging / CONFIG_DIR / "config.yaml"
    # Outputs land next to the -C config, but the mise shim resolves the
    # toolchain from the working directory: run from the source root so the
    # project's pinned ai-rulez is used even when the caller invoked this
    # script under a bare environment (a temp cwd would fall back to whatever
    # the ambient mise config provides).
    subprocess.run(
        [
            find_binary(),
            "generate",
            "--quiet",
            "--no-self-mcp",
            "--strict-config",
            "-C",
            str(config),
        ],
        cwd=source_root,
        check=True,
    )
    drop_unwanted(staging)


def drop_unwanted(root: Path) -> None:
    """Delete the unwanted outputs and remove them from the generation manifest."""
    for rel in DROPPED:
        (root / rel).unlink(missing_ok=True)
    # v5 also writes machine-local digests here; they are never committed
    # (.gitignore is Cobo-managed, so this cannot be ignored there), and the
    # committed manifest plus per-file Content-Hash lines are enough to verify
    # ownership without it.
    (root / CONFIG_DIR / ".generated-manifest.local.json").unlink(missing_ok=True)
    manifest = root / MANIFEST
    if not manifest.is_file():
        return
    data = json.loads(manifest.read_text(encoding="utf-8"))
    files = data.get("files", [])
    kept = [f for f in files if f not in DROPPED]
    if kept != files:
        data["files"] = kept
        # LF on every platform: .gitattributes checks it out as LF, and a CRLF
        # render on Windows would make --check report it as stale.
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def expected_files(root: Path) -> set[str]:
    """Return every output path recorded in ``root``'s manifest, plus the manifest."""
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    return {*data.get("files", []), MANIFEST}


def owned_files(root: Path) -> set[str]:
    """Return every generation-owned file currently present under ``root``."""
    found = {rel for rel in OWNED_FILES if (root / rel).is_file()}
    for owned in OWNED_DIRS:
        base = root / owned
        if base.is_dir():
            found.update(p.relative_to(root).as_posix() for p in base.rglob("*") if p.is_file())
    return found


def is_link(path: Path) -> bool:
    """True for symlinks and Windows directory junctions (reparse points).

    ``Path.is_symlink()`` misses junctions, but promotion must refuse both:
    either one would redirect writes outside the checkout. ``os.path``
    exposes junctions from Python 3.12 on; older interpreters fall back to
    symlinks alone.
    """
    if path.is_symlink():
        return True
    isjunction = getattr(os.path, "isjunction", None)
    return bool(isjunction is not None and isjunction(path))


def check_no_symlink(repo: Path, rel: str) -> None:
    """Refuse a promotion target that passes through a symlink or junction.

    ``copyfile``/``mkdir``/``unlink`` would otherwise follow the link and
    touch files outside the checkout, so a symlinked ``AGENTS.md`` or owned
    directory fails the run instead of corrupting an arbitrary user file.
    """
    current = repo
    for part in Path(rel).parts:
        current = current / part
        if is_link(current):
            sys.exit(f"error: refusing to promote through symlink: {current}")


def sync_exec_bit(src: Path, dest: Path) -> None:
    """Mirror the owner-execute bit from staging to the checkout (POSIX only).

    ``copyfile`` copies contents but not modes, so a generated helper script
    would lose ``+x`` on promote while content comparison still passes. Only
    the owner-execute bit is mirrored: it is the one Git tracks, and full
    modes are umask- and platform-dependent.
    """
    if os.name != "posix":
        return
    wanted = stat.S_IMODE(os.stat(src).st_mode) & 0o100
    current = stat.S_IMODE(os.stat(dest).st_mode)
    if bool(current & 0o100) != bool(wanted):
        os.chmod(dest, (current | 0o100) if wanted else (current & ~0o100))


def exec_bit_differs(src: Path, dest: Path) -> bool:
    """True when the owner-execute bits differ (POSIX only; see ``sync_exec_bit``)."""
    if os.name != "posix":
        return False
    src_exec = bool(stat.S_IMODE(os.stat(src).st_mode) & 0o100)
    dest_exec = bool(stat.S_IMODE(os.stat(dest).st_mode) & 0o100)
    return src_exec != dest_exec


def dir_is_fully_stale(dest: Path, repo: Path, removed: set[str]) -> bool:
    """True when everything under ``dest`` is stale-manifest-owned or nothing.

    Only then may promotion replace the directory with a generated file:
    anything else inside is hand-authored content that must be refused, not
    vaporized. Every entry counts, not just regular files: a link is owned
    only by its own recorded path (replacing it removes the link itself,
    never the target), and a subdirectory must itself be fully stale.
    """
    try:
        entries = list(dest.iterdir())
    except OSError:
        return False
    for entry in entries:
        rel = entry.relative_to(repo).as_posix()
        if is_link(entry):
            if rel not in removed:
                return False
        elif entry.is_dir():
            if not dir_is_fully_stale(entry, repo, removed):
                return False
        elif rel not in removed:
            return False
    return True


def sync(rendered: Path, repo: Path) -> list[str]:
    """Promote a staging ``rendered`` tree into ``repo``.

    Runs in two phases. First every destination is validated without writing
    anything: symlinks are refused, hand-authored collisions are refused, and
    file/directory transitions are either cleared (fully stale-manifest-owned)
    or refused. Then stale outputs are removed, files are copied, and the
    manifest replaced last, so a failure keeps the previous manifest and a
    retry recognizes the full previously generated set. Only previously
    generated files under the owned sets are ever removed; hand-added files
    stay for ``--check`` to report, and dropped side files are never touched.
    Returns the removed paths.
    """
    expected = expected_files(rendered)
    try:
        previous = expected_files(repo)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        previous = set()
    removed = sorted((previous & owned_files(repo)) - expected - set(DROPPED))
    removed_set = set(removed)
    replace_dirs: list[str] = []
    for rel in sorted(expected):
        check_no_symlink(repo, rel)
    for rel in removed:
        check_no_symlink(repo, rel)
    for rel in sorted(expected - {MANIFEST}):
        dest = repo / rel
        if dest.is_file() and not is_link(dest):
            if rel not in previous and not filecmp.cmp(
                rendered / rel, dest, shallow=False
            ):
                sys.exit(
                    f"error: refusing to overwrite hand-authored {rel}: it is "
                    "absent from the previous manifest and differs from the "
                    "rendered output. Move it aside and re-run, or delete it "
                    "to adopt the generated file."
                )
        elif dest.is_dir() and not is_link(dest):
            if dir_is_fully_stale(dest, repo, removed_set):
                replace_dirs.append(rel)
            else:
                sys.exit(
                    f"error: cannot promote {rel}: {rel} is a directory "
                    "holding files generation does not own. Remove it and "
                    "re-run, or move its hand-authored content aside first."
                )
        parts = Path(rel).parts[:-1]
        for depth in range(1, len(parts) + 1):
            ancestor = Path(*parts[:depth]).as_posix()
            if (repo / ancestor).is_file() and ancestor not in removed_set:
                sys.exit(
                    f"error: cannot promote {rel}: parent {ancestor} is a "
                    "file generation does not own. Remove it and re-run."
                )
    for rel in replace_dirs:
        shutil.rmtree(repo / rel)
    for rel in removed:
        (repo / rel).unlink(missing_ok=True)
    for rel in sorted(expected - {MANIFEST}):
        dest = repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rendered / rel, dest)
        sync_exec_bit(rendered / rel, dest)
    dest = repo / MANIFEST
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(rendered / MANIFEST, dest)
    sync_exec_bit(rendered / MANIFEST, dest)
    return removed


def compare(rendered: Path, repo: Path) -> list[str]:
    """Describe how ``repo``'s outputs differ from a fresh render in ``rendered``."""
    expected = expected_files(rendered)
    try:
        previous = expected_files(repo)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        previous = set()
    owned = owned_files(repo)
    problems = []
    for rel in sorted(expected):
        target = repo / rel
        if not target.is_file():
            problems.append(f"missing: {rel}")
        elif not filecmp.cmp(rendered / rel, target, shallow=False):
            problems.append(f"stale: {rel}")
        elif exec_bit_differs(rendered / rel, target):
            problems.append(f"stale mode: {rel}")
    leftover = owned - expected - set(DROPPED)
    problems.extend(f"not generated: {rel}" for rel in sorted(leftover))
    # A previously generated file outside the owned sets (say, a Copilot
    # instruction file from a removed preset) is neither promoted nor removed:
    # the maintainer may have adopted it by hand. Report it instead of
    # silently passing with obsolete instructions active; one promote run
    # retires the report by refreshing the manifest.
    for rel in sorted(previous - expected - set(DROPPED) - owned):
        if (repo / rel).is_file():
            problems.append(f"orphaned: {rel}")
    # A dropped file reappearing (say, a hand-written CLAUDE.md) would shadow or
    # contradict AGENTS.md for the agent that reads it.
    problems.extend(f"unwanted: {rel}" for rel in DROPPED if (repo / rel).is_file())
    return problems


def check() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        render(REPO, work)
        problems = compare(work, REPO)
    if problems:
        print("Generated agent files are out of date with .ai-rulez/:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("Run `mise run agents:generate` and commit the result.", file=sys.stderr)
        return 1
    return 0


def generate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        render(REPO, work)
        removed = sync(work, REPO)
    for rel in removed:
        print(f"removed stale output: {rel}")


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
    generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
