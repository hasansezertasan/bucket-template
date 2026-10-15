# Scoop Bucket Development Guide

This repository is a Scoop bucket generated from
[`bucket-template`](https://github.com/hasansezertasan/bucket-template). Keep
scripts and workflows owner-neutral and package-neutral: repository identity
comes from the Git remote, GitHub Actions context, or an explicit
environment/CLI override.

Skills for operating the bucket (adding, fixing, triaging, removing, and
verifying manifests) come from the
[`scoop-bucket-skills`](https://github.com/hasansezertasan/scoop-bucket-skills)
Claude Code plugin. Install it, or read its `SKILL.md` files directly when a
task matches one.

## Layout

- `bucket/*.json` contains installable Scoop manifests. A new bucket starts
  empty; `bucket/.gitkeep` retains the directory.
- `scripts/update_manifests.py` updates versions, URLs, and hashes without
  changing curated metadata.
- `scripts/gen_readme_packages.py` owns the generated README package table.
- `.github/workflows/` validates, installs, and updates manifests.

## Invariants

- Use the `scoop-add` scaffolder from the plugin rather than hand-writing a new
  manifest.
- Keep `checkver` and `autoupdate` aligned with the concrete download URL.
- Never interpolate an untrusted dispatch payload directly into shell source.
- Keep workflows least-privileged: every workflow starts with `permissions: {}`
  and each job opts in. Write access is limited to the update and Cobo-sync
  jobs, the `zizmor` SARIF upload (`security-events`), and the two lint
  workflows' sticky PR comments (`pull_request_target`, which never checks out
  PR code). Do not rely on the repository's default workflow permissions.
- A binary manifest with a placeholder hash (all zeroes) must not be installed by CI.
- For shim manifests, `scripts/noop.ps1`, its generated SHA-256, and its raw
  repository URL must agree.
- Regenerate the README table after any manifest change.
- Do not manually edit `.gitignore`; it is managed by Cobo and `cobo.lock`.
- Files tracked by `.copier-answers.yml` come from the template; pull template
  changes with `copier update` instead of editing them to diverge.

## Commands

```sh
mise install
mise run check
```

The Windows install workflow assumes `<command> version`. Add package-specific
commands to its `$smoke` map when needed.
