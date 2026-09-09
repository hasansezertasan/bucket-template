"""Shared HTTP request helpers for the bucket maintenance scripts."""

from __future__ import annotations

import json
import os
import urllib.request
from urllib.parse import urlsplit

USER_AGENT = "scoop-bucket-maintenance"


def request(url: str, *, accept: str = "application/json") -> urllib.request.Request:
    """Build a request and send credentials only to GitHub's exact API host."""
    req = urllib.request.Request(url)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", USER_AGENT)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and urlsplit(url).hostname == "api.github.com":
        req.add_header("Authorization", f"Bearer {token}")
    return req


def get_json(url: str) -> dict:
    """Fetch and decode a JSON document."""
    with urllib.request.urlopen(request(url), timeout=30) as response:  # noqa: S310
        return json.load(response)
