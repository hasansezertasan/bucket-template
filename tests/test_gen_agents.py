"""Tests for ``scripts/gen_agents.py`` (stdlib ``unittest``, no ai-rulez binary).

Exercises the post-processing and drift comparison on synthetic trees. Run with
``python -m unittest discover -s tests`` from the repo root.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import unittest
import unittest.mock
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import gen_agents as gen  # noqa: E402

OUTPUTS = ["AGENTS.md", ".agents/skills/demo/SKILL.md", ".claude/skills/demo/SKILL.md"]


def write(root: Path, rel: str, text: str = "x\n") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render(root: Path, files: list[str]) -> None:
    """Lay out ``files`` plus a manifest listing them, as ai-rulez would."""
    for rel in files:
        write(root, rel)
    write(root, gen.MANIFEST, json.dumps({"version": "1", "files": files}))


class DropUnwantedTest(unittest.TestCase):
    def test_removes_files_and_manifest_entries(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            render(root, [*gen.DROPPED, *OUTPUTS])
            gen.drop_unwanted(root)
            for rel in gen.DROPPED:
                self.assertFalse((root / rel).exists(), rel)
            self.assertEqual(gen.expected_files(root), {*OUTPUTS, gen.MANIFEST})

    def test_rewrites_manifest_with_lf(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            render(root, [*gen.DROPPED, *OUTPUTS])
            gen.drop_unwanted(root)
            self.assertNotIn(b"\r", (root / gen.MANIFEST).read_bytes())

    def test_tolerates_missing_file_and_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            gen.drop_unwanted(Path(tmp))

    def test_removes_local_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            render(root, OUTPUTS)
            write(root, f"{gen.CONFIG_DIR}/.generated-manifest.local.json", "{}\n")
            gen.drop_unwanted(root)
            self.assertFalse(
                (root / f"{gen.CONFIG_DIR}/.generated-manifest.local.json").exists()
            )
            self.assertEqual(gen.expected_files(root), {*OUTPUTS, gen.MANIFEST})


class CompareTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name)
        self.rendered, self.repo = base / "rendered", base / "repo"
        render(self.rendered, OUTPUTS)
        render(self.repo, OUTPUTS)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_identical_trees_pass(self) -> None:
        self.assertEqual(gen.compare(self.rendered, self.repo), [])

    def test_reports_stale_file(self) -> None:
        write(self.repo, "AGENTS.md", "hand edit\n")
        self.assertEqual(gen.compare(self.rendered, self.repo), ["stale: AGENTS.md"])

    def test_reports_missing_file(self) -> None:
        (self.repo / OUTPUTS[1]).unlink()
        self.assertEqual(gen.compare(self.rendered, self.repo), [f"missing: {OUTPUTS[1]}"])

    def test_reports_leftover_file_in_owned_dir(self) -> None:
        write(self.repo, ".agents/skills/old/SKILL.md")
        self.assertEqual(
            gen.compare(self.rendered, self.repo),
            ["not generated: .agents/skills/old/SKILL.md"],
        )

    def test_reports_root_file_no_longer_generated(self) -> None:
        render(self.rendered, OUTPUTS[1:])
        self.assertEqual(
            gen.compare(self.rendered, self.repo),
            [f"stale: {gen.MANIFEST}", "not generated: AGENTS.md"],
        )

    def test_reports_unwanted_root_files(self) -> None:
        write(self.repo, "CLAUDE.md")
        write(self.repo, "GEMINI.md")
        self.assertEqual(
            gen.compare(self.rendered, self.repo),
            ["unwanted: CLAUDE.md", "unwanted: GEMINI.md"],
        )

    def test_ignores_claude_files_outside_skills(self) -> None:
        write(self.repo, ".claude/settings.local.json", "{}\n")
        self.assertEqual(gen.compare(self.rendered, self.repo), [])

    def test_reports_orphaned_previous_output(self) -> None:
        # A file the previous manifest lists outside the owned sets (say, an
        # instruction file from a removed preset) is reported, not silently
        # passed, and never auto-deleted: the maintainer may have adopted it.
        # The manifest itself reports stale alongside, and one promote run
        # retires both by refreshing it.
        render(self.repo, [*OUTPUTS, "COPILOT.md"])
        write(self.repo, "COPILOT.md")
        self.assertEqual(
            gen.compare(self.rendered, self.repo),
            [f"stale: {gen.MANIFEST}", "orphaned: COPILOT.md"],
        )

    def test_ignores_absent_previous_output(self) -> None:
        render(self.repo, [*OUTPUTS, "COPILOT.md"])
        (self.repo / "COPILOT.md").unlink()
        self.assertEqual(gen.compare(self.rendered, self.repo), [f"stale: {gen.MANIFEST}"])


class RenderTest(unittest.TestCase):
    def test_runs_project_toolchain_from_source_root(self) -> None:
        # Regression lock: the mise shim resolves the ai-rulez version from
        # the working directory, so render must run from the source root
        # (where .config/mise.toml pins it) rather than the staging copy —
        # otherwise a bare environment falls back to whatever ambient config
        # provides (once an ancient npm-wrapped v4).
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, staging = base / "src", base / "staging"
            staging.mkdir()
            with (
                unittest.mock.patch.object(gen.subprocess, "run") as run,
                unittest.mock.patch.object(
                    gen.shutil, "which", return_value="/bin/ai-rulez"
                ),
                unittest.mock.patch.object(gen.shutil, "copytree"),
            ):
                gen.render(source, staging)
            argv, kwargs = run.call_args.args, run.call_args.kwargs
            self.assertEqual(argv[0][0], "/bin/ai-rulez")
            self.assertIn("--no-self-mcp", argv[0])
            self.assertIn("--strict-config", argv[0])
            self.assertEqual(kwargs.get("cwd"), source)
            config_flag = argv[0][argv[0].index("-C") + 1]
            self.assertTrue(
                config_flag.startswith(str(staging)),
                f"config must stay inside staging, got {config_flag!r}",
            )


class SyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name)
        self.rendered, self.repo = base / "rendered", base / "repo"
        render(self.rendered, OUTPUTS)
        render(self.repo, OUTPUTS)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_promotes_rendered_files(self) -> None:
        write(self.repo, "AGENTS.md", "hand edit\n")
        (self.repo / OUTPUTS[1]).unlink()
        removed = gen.sync(self.rendered, self.repo)
        self.assertEqual(removed, [])
        self.assertEqual(gen.compare(self.rendered, self.repo), [])

    def test_removes_previously_generated_stale_files(self) -> None:
        stale = ".agents/skills/old/SKILL.md"
        render(self.repo, [*OUTPUTS, stale])
        removed = gen.sync(self.rendered, self.repo)
        self.assertEqual(removed, [stale])
        self.assertFalse((self.repo / stale).exists())

    def test_keeps_hand_added_files_for_check_to_report(self) -> None:
        extra = ".agents/skills/handadded/SKILL.md"
        write(self.repo, extra)
        removed = gen.sync(self.rendered, self.repo)
        self.assertEqual(removed, [])
        self.assertTrue((self.repo / extra).is_file())
        self.assertEqual(
            gen.compare(self.rendered, self.repo), [f"not generated: {extra}"]
        )

    def test_never_deletes_dropped_files(self) -> None:
        render(self.repo, [*OUTPUTS, "CLAUDE.md"])
        write(self.repo, "CLAUDE.md")
        removed = gen.sync(self.rendered, self.repo)
        self.assertEqual(removed, [])
        self.assertTrue((self.repo / "CLAUDE.md").is_file())

    def test_tolerates_missing_repo_manifest(self) -> None:
        base = Path(self._tmp.name)
        fresh, bare = base / "fresh", base / "bare"
        render(fresh, OUTPUTS)
        bare.mkdir()
        removed = gen.sync(fresh, bare)
        self.assertEqual(removed, [])
        self.assertEqual(gen.compare(fresh, bare), [])

    def test_refuses_symlinked_destination(self) -> None:
        outside = Path(self._tmp.name) / "outside.txt"
        outside.write_text("precious\n", encoding="utf-8")
        (self.repo / OUTPUTS[0]).unlink()
        (self.repo / OUTPUTS[0]).symlink_to(outside)
        with self.assertRaises(SystemExit):
            gen.sync(self.rendered, self.repo)
        self.assertEqual(outside.read_text(encoding="utf-8"), "precious\n")

    def test_refuses_symlinked_owned_parent(self) -> None:
        elsewhere = Path(self._tmp.name) / "elsewhere"
        elsewhere.mkdir()
        shutil.rmtree(self.repo / ".agents")
        (self.repo / ".agents").symlink_to(elsewhere)
        with self.assertRaises(SystemExit):
            gen.sync(self.rendered, self.repo)
        self.assertEqual(list(elsewhere.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "executable-bit semantics")
    def test_promotes_executable_bit(self) -> None:
        staged = self.rendered / OUTPUTS[1]
        staged.chmod(0o755)
        gen.sync(self.rendered, self.repo)
        self.assertTrue(os.stat(self.repo / OUTPUTS[1]).st_mode & 0o100)

    @unittest.skipUnless(os.name == "posix", "executable-bit semantics")
    def test_reports_mode_drift(self) -> None:
        (self.repo / OUTPUTS[0]).chmod(0o755)
        self.assertEqual(
            gen.compare(self.rendered, self.repo), [f"stale mode: {OUTPUTS[0]}"]
        )


if __name__ == "__main__":
    unittest.main()
