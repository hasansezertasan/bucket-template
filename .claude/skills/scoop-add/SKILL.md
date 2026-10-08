---
description: Use when adding a PyPI shim or prebuilt Windows binary manifest to this Scoop bucket.
name: scoop-add
user_invocable: false
# Content-Hash: blake3:2f994b835c534b0151c96143aef7178787edbbc4dca85a87b4794dd92d0f0bcc
# Source-Hash: blake3:0e939efc60d70d578854a9b2266107aff73444cfd9cb7ee93b3bc6c73bf551e4
---

# Add a Scoop Manifest

Use `scripts/add_manifest.py`; do not create a manifest from scratch. First choose
the route from what upstream publishes:

| Upstream artifact | Route | Command |
| --- | --- | --- |
| Python CLI on PyPI | shim | `mise run add-manifest shim <package>` |
| Prebuilt Windows `.zip` | binary | `mise run add-manifest binary <owner>/<repository>` |
| Both | both | run both commands; use `--via pipx` for the shim sibling |

For a shim, `uv` is the default. `--via pipx` gives the manifest a `-pipx`
suffix. The script infers the bucket's GitHub repository from `origin` so the
manifest can download `scripts/noop.ps1`; pass `--bucket-repository` when that
cannot be inferred.

For a binary, the script fetches the latest GitHub release, selects a `.zip`,
computes SHA-256, and inspects the archive for `extract_dir` and `bin`. Use
`--artifact` when several archives exist. Before the first release, use `--seed`
with `--bin` and verify the assumed tag and filename pattern later.

After scaffolding:

1. Review the description, SPDX license, URL pattern, executable, and archive
   layout.
2. Invoke `scoop-verify` for the pre-PR gate: noop URL/hash consistency,
   placeholder handling, smoke commands, README generation, local checks, and
   Windows install evidence. If skills are not auto-discovered, read
   `.agents/skills/scoop-verify/SKILL.md` and follow it.

Keep one package family per pull request and include verification in the PR body.
