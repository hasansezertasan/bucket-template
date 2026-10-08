"""Tests for ``scripts/gen_agents.py`` (stdlib ``unittest``, no ai-rulez binary).

Exercises the post-processing and drift comparison on synthetic trees. Run with
``python -m unittest discover -s tests`` from the repo root.
"""

from __future__ import annotations

import json
import sys
import unittest
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

    def test_tolerates_missing_file_and_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            gen.drop_unwanted(Path(tmp))


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
        self.assertEqual(gen.compare(self.rendered, self.repo), ["not generated: AGENTS.md"])

    def test_reports_unwanted_root_files(self) -> None:
        write(self.repo, "CLAUDE.md")
        write(self.repo, ".agents/settings.json", "{}\n")
        self.assertEqual(
            gen.compare(self.rendered, self.repo),
            ["unwanted: CLAUDE.md", "unwanted: .agents/settings.json"],
        )

    def test_ignores_claude_files_outside_skills(self) -> None:
        write(self.repo, ".claude/settings.local.json", "{}\n")
        self.assertEqual(gen.compare(self.rendered, self.repo), [])


if __name__ == "__main__":
    unittest.main()
