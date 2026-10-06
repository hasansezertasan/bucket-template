# Scoop Bucket Development Guide

This repository is a reusable Scoop bucket. Keep it owner-neutral and
package-neutral: repository identity must come from the Git remote, GitHub
Actions context, or an explicit environment/CLI override.

## Layout

- `bucket/*.json` contains installable Scoop manifests. The template starts
  empty; `bucket/.gitkeep` retains the directory.
- `scripts/add_manifest.py` scaffolds binary and PyPI shim manifests.
- `scripts/update_manifests.py` updates versions, URLs, and hashes without
  changing curated metadata.
- `scripts/gen_readme_packages.py` owns the generated README package table.
- `.github/workflows/` validates, installs, and updates manifests.

## Invariants

- Use the scaffolder rather than hand-writing a new manifest.
- Keep `checkver` and `autoupdate` aligned with the concrete download URL.
- Never interpolate an untrusted dispatch payload directly into shell source.
- Keep workflows least-privileged; only update jobs receive write access.
- A binary manifest with a placeholder hash (all zeroes) must not be installed by CI.
- For shim manifests, `scripts/noop.ps1`, its generated SHA-256, and its raw
  repository URL must agree.
- Regenerate the README table after any manifest change.
- Do not manually edit `.gitignore`; it is managed by Cobo and `cobo.lock`.

## Commands

```sh
mise run add-manifest shim <package>
mise run add-manifest binary <owner>/<repository>
mise install
mise run check
```

The Windows install workflow assumes `<command> version`. Add package-specific
commands to its `$smoke` map when needed.
