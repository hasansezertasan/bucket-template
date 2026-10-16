# Update Manifests with a Tested Python Script

## Context and Problem Statement

Scoop ships no update tooling: bumping a manifest means fetching the upstream
version, rebuilding download URLs from the `autoupdate` template, downloading
assets, computing SHA-256 hashes, and rewriting JSON — for binary, pipx-shim,
and uv-tool-shim routes alike. That logic must live either as inline shell in
the update workflows or as a script the workflows call.

## Considered Options

* Keep the logic as inline shell in each workflow
* Extract a shared, unit-tested Python update script

## Decision Outcome

Chosen option: "Extract a tested Python script." `scripts/update_manifests.py`
(with `url_fetch.py` underneath) owns version checks, URL rebuilds, hash
fetches, and the no-rollback rule for yanked releases; `tests/` unit-tests it
with stdlib `unittest` and no network. The script never commits —
`peter-evans/create-pull-request` opens the pull request from the diff, so the
same code path serves the scheduled workflow, the dispatch workflow, and local
runs. Inline shell would duplicate the three-route, two-source logic across the
scheduled and dispatch workflows with nothing testing it.

### Consequences

* Good, because the trickiest logic (hash fetching, family-prefix matching,
  rollback refusal) is unit-tested offline.
* Good, because a contributor can run the updater locally exactly as CI does.
* Bad, because the bucket carries a second language runtime beside its
  PowerShell/JSON payload (pinned to `python = "3.15.0"` in `.config/mise.toml`
  to keep it reproducible).

Related research: [0001-homebrew-tap-template-comparison](../research/0001-homebrew-tap-template-comparison.md).
