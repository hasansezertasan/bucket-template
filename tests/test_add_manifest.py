"""Tests for ``scripts/add_manifest.py`` (stdlib ``unittest``, no network).

Network calls (PyPI, the GitHub API, the asset download) are mocked, so the
suite exercises the pure rendering/inference logic offline. Run with
``python -m unittest discover -s tests`` from the repo root.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys
import types
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import add_manifest as am  # noqa: E402


class HelperTest(unittest.TestCase):
    def test_normalize(self) -> None:
        self.assertEqual(am.normalize("Foo_Bar.Baz"), "foo-bar-baz")

    def test_clean_desc_strips_article_and_period(self) -> None:
        self.assertEqual(am.clean_desc("A neat tool."), "Neat tool")

    def test_clean_desc_capitalizes(self) -> None:
        self.assertEqual(am.clean_desc("generic CLI"), "Generic CLI")

    def test_parse_repo_owner_repo(self) -> None:
        self.assertEqual(am.parse_repo("o/r"), ("o", "r"))

    def test_parse_repo_url_strips_git(self) -> None:
        self.assertEqual(am.parse_repo("https://github.com/o/r.git"), ("o", "r"))

    def test_parse_repo_rejects_garbage(self) -> None:
        with self.assertRaises(SystemExit):
            am.parse_repo("not-a-repo")

    def test_spdx_from_github_meta(self) -> None:
        self.assertEqual(am.spdx_license({"license": {"spdx_id": "MIT"}}), "MIT")

    def test_spdx_noassertion_falls_back(self) -> None:
        self.assertEqual(
            am.spdx_license({"license": {"spdx_id": "NOASSERTION"}}),
            "TODO-set-SPDX-license",
        )

    def test_pypi_homepage_prefers_case_insensitive_homepage(self) -> None:
        info = {"project_urls": {"homepage": "https://github.com/o/r",
                                 "source": "https://github.com/o/r.git"}}
        self.assertEqual(am.pypi_homepage(info, "r"), "https://github.com/o/r")

    def test_pypi_homepage_falls_back_to_source_without_git(self) -> None:
        info = {"project_urls": {"source": "https://github.com/o/r.git"}}
        self.assertEqual(am.pypi_homepage(info, "r"), "https://github.com/o/r")

    def test_pypi_homepage_default_is_pypi(self) -> None:
        self.assertEqual(am.pypi_homepage({}, "r"), "https://pypi.org/project/r/")

    def test_pypi_license_prefers_expression(self) -> None:
        self.assertEqual(am.pypi_license({"license_expression": "MIT"}), "MIT")

    def test_templatize_replaces_version(self) -> None:
        self.assertEqual(am.templatize("v1.2.3", "1.2.3"), "v$version")

    def test_templatize_warns_when_absent(self) -> None:
        buf = io.StringIO()
        with mock.patch("sys.stderr", buf):
            self.assertEqual(am.templatize("static.zip", "1.2.3"), "static.zip")
        self.assertIn("won't auto-update", buf.getvalue())

    def test_noop_source_uses_bucket_repository_and_file_hash(self) -> None:
        url, sha = am.noop_source("acme/scoop-tools", "stable")
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/acme/scoop-tools/stable/scripts/noop.ps1",
        )
        expected_sha = hashlib.sha256(
            am.NOOP_FILE.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        self.assertEqual(sha, expected_sha)

    def test_noop_source_hashes_canonical_lf_even_with_crlf_input(self) -> None:
        with mock.patch.object(
            am.Path, "read_bytes", return_value=b"Write-Output hello\r\n"
        ):
            _, sha = am.noop_source("acme/scoop-tools", "stable")
        expected = hashlib.sha256(b"Write-Output hello\n").hexdigest()
        self.assertEqual(sha, expected)

    def test_noop_source_rejects_invalid_repository(self) -> None:
        with self.assertRaises(SystemExit):
            am.noop_source("not-a-repository")


def _zip_bytes(entries: list[str]) -> str:
    """Write a throwaway .zip containing ``entries`` and return its path."""
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".zip")
    import os

    os.close(fd)
    with zipfile.ZipFile(path, "w") as archive:
        for name in entries:
            archive.writestr(name, b"x")
    return path


class InspectZipTest(unittest.TestCase):
    def _inspect(self, entries: list[str], token: str):
        import os

        path = _zip_bytes(entries)
        self.addCleanup(lambda: os.unlink(path))
        return am.inspect_zip(path, token)

    def test_single_wrapping_folder_and_lone_exe(self) -> None:
        extract_dir, exe, hint = self._inspect(
            ["widget/widget.exe", "widget/data.bin"], "widget")
        self.assertEqual(extract_dir, "widget")
        self.assertEqual(exe, "widget.exe")
        self.assertEqual(hint, "")

    def test_no_wrapping_folder(self) -> None:
        extract_dir, exe, _ = self._inspect(["tool.exe", "readme.txt"], "tool")
        self.assertIsNone(extract_dir)
        self.assertEqual(exe, "tool.exe")

    def test_nested_exe_keeps_path_relative_to_wrapper(self) -> None:
        # tool/bin/tool.exe under a stripped `extract_dir: tool` must yield
        # `bin/tool.exe`, not `tool.exe` (which wouldn't exist post-extract).
        extract_dir, exe, hint = self._inspect(
            ["tool/bin/tool.exe", "tool/README"], "tool")
        self.assertEqual(extract_dir, "tool")
        self.assertEqual(exe, "bin/tool.exe")
        self.assertIn("nested", hint)

    def test_nested_exe_no_wrapper(self) -> None:
        _, exe, _ = self._inspect(["bin/tool.exe", "readme.txt"], "tool")
        self.assertEqual(exe, "bin/tool.exe")

    def test_multiple_exes_matches_token(self) -> None:
        _, exe, hint = self._inspect(
            ["app/app.exe", "app/helper.exe"], "app")
        self.assertEqual(exe, "app.exe")
        self.assertEqual(hint, "")

    def test_multiple_exes_no_match_returns_hint(self) -> None:
        _, exe, hint = self._inspect(["a.exe", "b.exe"], "c")
        self.assertIsNone(exe)
        self.assertIn("multiple .exe", hint)

    def test_no_exe_returns_hint(self) -> None:
        _, exe, hint = self._inspect(["readme.txt"], "tool")
        self.assertIsNone(exe)
        self.assertIn("no .exe", hint)


class SelectZipTest(unittest.TestCase):
    def test_lone_zip(self) -> None:
        asset = {"name": "app-windows.zip"}
        self.assertIs(am.select_zip([asset, {"name": "notes.txt"}], None), asset)

    def test_explicit_artifact(self) -> None:
        a, b = {"name": "x.zip"}, {"name": "y.zip"}
        self.assertIs(am.select_zip([a, b], "y.zip"), b)

    def test_multiple_zips_without_choice_exits(self) -> None:
        with self.assertRaises(SystemExit):
            am.select_zip([{"name": "a.zip"}, {"name": "b.zip"}], None)

    def test_no_assets_exits(self) -> None:
        with self.assertRaises(SystemExit):
            am.select_zip([], None)


class RenderTest(unittest.TestCase):
    def test_shim_uv_shape(self) -> None:
        data = am.render_shim(
            am.ShimManifestSpec(
                package="gizmo",
                installer="uv",
                description="Demo (uv tool install)",
                homepage="https://github.com/o/gizmo",
                license_id="MIT",
                version="1.0.0",
                noop_url="https://example.com/noop.ps1",
                noop_hash="a" * 64,
            )
        )
        self.assertEqual(
            list(data),
            ["version", "description", "homepage", "license", "depends", "url",
             "hash", "installer", "uninstaller", "checkver", "autoupdate"],
        )
        self.assertEqual(data["depends"], "uv")
        self.assertEqual(data["installer"]["script"],
                         "uv tool install gizmo==$version --force")
        self.assertEqual(data["uninstaller"]["script"], "uv tool uninstall gizmo")
        self.assertEqual(data["url"], "https://example.com/noop.ps1")
        self.assertEqual(data["hash"], "a" * 64)

    def test_shim_pipx_uses_pipx_commands(self) -> None:
        data = am.render_shim(
            am.ShimManifestSpec(
                package="widget",
                installer="pipx",
                description="Demo (pipx install)",
                homepage="https://github.com/o/widget",
                license_id="MIT",
                version="1.0.0",
                noop_url="https://example.com/noop.ps1",
                noop_hash="a" * 64,
            )
        )
        self.assertEqual(data["depends"], "pipx")
        self.assertEqual(data["installer"]["script"],
                         "pipx install widget==$version --force")
        self.assertEqual(data["uninstaller"]["script"], "pipx uninstall widget")

    def test_binary_shape_and_extract_dir(self) -> None:
        data = am.render_binary(
            am.BinaryManifestSpec(
                token="widget",
                repository_url="https://github.com/o/widget",
                description="Demo",
                license_id="MIT",
                version="1.0.0",
                download_url="https://github.com/o/widget/releases/download/v1.0.0/widget-windows.zip",
                sha256="a" * 64,
                extract_dir="widget",
                executable="widget.exe",
                autoupdate_url="https://github.com/o/widget/releases/download/v$version/widget-windows.zip",
            )
        )
        self.assertEqual(
            list(data),
            ["version", "description", "homepage", "license", "architecture",
             "bin", "shortcuts", "checkver", "autoupdate"],
        )
        self.assertEqual(data["architecture"]["64bit"]["extract_dir"], "widget")
        self.assertEqual(data["bin"], "widget.exe")
        self.assertEqual(data["shortcuts"], [["widget.exe", "widget"]])
        self.assertEqual(data["checkver"], {"github": "https://github.com/o/widget"})

    def test_binary_omits_extract_dir_when_none(self) -> None:
        data = am.render_binary(
            am.BinaryManifestSpec(
                token="tool",
                repository_url="https://github.com/o/tool",
                description="Demo",
                license_id="MIT",
                version="1.0.0",
                download_url="u",
                sha256="a" * 64,
                extract_dir=None,
                executable="tool.exe",
                autoupdate_url="u",
            )
        )
        self.assertNotIn("extract_dir", data["architecture"]["64bit"])


class AddShimTest(unittest.TestCase):
    def _run(self, info: dict, **ns):
        captured = {}
        stderr = io.StringIO()
        fields = {
            "package": "pkg",
            "via": "uv",
            "name": None,
            "homepage": None,
            "bucket_repository": "acme/scoop-bucket",
            "bucket_ref": "main",
            **ns,
        }
        args = types.SimpleNamespace(**fields)
        with (
            mock.patch.object(am, "pypi_info", return_value=info),
            mock.patch.object(am, "_write_manifest",
                              side_effect=lambda n, d: captured.update(name=n, data=d)
                              or Path(f"bucket/{n}.json")),
            mock.patch("sys.stdout", io.StringIO()),
            mock.patch("sys.stderr", stderr),
        ):
            am.add_shim(args)
        captured["stderr"] = stderr.getvalue()
        return captured

    def test_uv_uses_bare_name(self) -> None:
        cap = self._run({"name": "gizmo", "version": "1.0.0", "summary": "Demo tool",
                         "project_urls": {"homepage": "https://github.com/o/gizmo"}})
        self.assertEqual(cap["name"], "gizmo")
        self.assertEqual(cap["data"]["description"], "Demo tool (uv tool install)")

    def test_pipx_appends_suffix(self) -> None:
        cap = self._run({"name": "widget", "version": "1.0.0", "summary": "Demo"},
                        via="pipx")
        self.assertEqual(cap["name"], "widget-pipx")
        self.assertEqual(cap["data"]["depends"], "pipx")
        self.assertTrue(cap["data"]["description"].endswith("(pipx install)"))

    def test_next_step_regenerates_readme_catalog(self) -> None:
        cap = self._run({"name": "widget", "version": "1.0.0", "summary": "Demo"})
        self.assertIn("mise run generate-readme", cap["stderr"])


class WriteManifestTest(unittest.TestCase):
    def _tmp_bucket(self) -> Path:
        import tempfile

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_rejects_path_separator(self) -> None:
        with mock.patch.object(am, "BUCKET", self._tmp_bucket()):
            with self.assertRaises(SystemExit):
                am._write_manifest("../evil", {})

    def test_refuses_existing(self) -> None:
        # Self-contained: create the collision in a temp bucket rather than
        # depending on a real manifest in bucket/ (which would also risk the
        # write escaping into the working tree if that file were ever removed).
        bucket = self._tmp_bucket()
        (bucket / "dupe.json").write_text("{}", encoding="utf-8")
        with mock.patch.object(am, "BUCKET", bucket):
            with self.assertRaises(SystemExit):
                am._write_manifest("dupe", {})

    def test_writes_into_patched_bucket(self) -> None:
        bucket = self._tmp_bucket()
        with mock.patch.object(am, "BUCKET", bucket):
            out = am._write_manifest("newpkg", {"version": "1.0.0"})
        self.assertTrue(out.exists())
        self.assertEqual(out.read_text().rstrip("\n"), '{\n    "version": "1.0.0"\n}')


class PypiInfoTest(unittest.TestCase):
    def test_404_exits_cleanly(self) -> None:
        err = urllib.error.HTTPError("u", 404, "Not Found", {}, None)  # type: ignore[arg-type]
        with mock.patch.object(am, "fetch_json", side_effect=err):
            with self.assertRaises(SystemExit):
                am.pypi_info("nope")


class AddBinaryTest(unittest.TestCase):
    def test_add_binary_rebases_exe_with_extract_dir_override(self) -> None:
        meta = {"html_url": "https://github.com/o/r", "description": "tool"}
        release = {
            "tag_name": "v1.0.0",
            "assets": [{"name": "tool.zip", "browser_download_url": "https://example/tool.zip"}],
        }
        args = argparse.Namespace(
            repo="o/r",
            name="tool",
            seed=False,
            artifact="tool.zip",
            extract_dir="dist",
            bin=None,
        )
        written = {}

        def fake_write(name: str, data: dict) -> Path:
            written["name"] = name
            written["data"] = data
            return Path(f"bucket/{name}.json")

        with (
            mock.patch.object(am, "fetch_json", side_effect=[meta, release]),
            mock.patch.object(am, "download_zip", return_value="/tmp/fake.zip"),
            mock.patch.object(am, "sha256_of_file", return_value="0" * 64),
            mock.patch.object(am, "inspect_zip", return_value=(None, "dist/tool.exe", "")),
            mock.patch.object(am, "_write_manifest", side_effect=fake_write),
            mock.patch("os.unlink"),
            mock.patch("sys.stdout"),
            mock.patch("sys.stderr"),
        ):
            am.add_binary(args)

        self.assertEqual(written["data"]["architecture"]["64bit"]["extract_dir"], "dist")
        self.assertEqual(written["data"]["bin"], "tool.exe")

    def test_add_binary_fails_when_exe_outside_extract_dir_and_no_bin(self) -> None:
        meta = {"html_url": "https://github.com/o/r", "description": "tool"}
        release = {
            "tag_name": "v1.0.0",
            "assets": [{"name": "tool.zip", "browser_download_url": "https://example/tool.zip"}],
        }
        args = argparse.Namespace(
            repo="o/r",
            name="tool",
            seed=False,
            artifact="tool.zip",
            extract_dir="other",
            bin=None,
        )

        with (
            mock.patch.object(am, "fetch_json", side_effect=[meta, release]),
            mock.patch.object(am, "download_zip", return_value="/tmp/fake.zip"),
            mock.patch.object(am, "sha256_of_file", return_value="0" * 64),
            mock.patch.object(am, "inspect_zip", return_value=(None, "dist/tool.exe", "")),
            mock.patch("os.unlink"),
            mock.patch("sys.stderr"),
            self.assertRaises(SystemExit),
        ):
            am.add_binary(args)


if __name__ == "__main__":
    unittest.main()
