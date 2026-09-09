"""Tests for authenticated HTTP request construction."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import url_fetch  # noqa: E402


class RequestTest(unittest.TestCase):
    def test_github_token_is_sent_only_to_exact_api_host(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "secret"}):
            api = url_fetch.request("https://api.github.com/repos/acme/widget")
            spoof = url_fetch.request(
                "https://evil.example/api.github.com/pypi.org/widget"
            )
            pypi = url_fetch.request("https://pypi.org/pypi/widget/json")

        self.assertTrue(api.has_header("Authorization"))
        self.assertFalse(spoof.has_header("Authorization"))
        self.assertFalse(pypi.has_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
