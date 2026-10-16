# Comparison with copier-homebrew-tap

Research snapshot: 2026-10-16, against
[hasansezertasan/copier-homebrew-tap](https://github.com/hasansezertasan/copier-homebrew-tap)
at `9d66ec9` (this repository at `646ca8f`). Claims below come from cloning it
and diffing it against this repository file by file.

## Goal

Find what the sibling Copier template for a Homebrew tap does better, and decide
which differences are real platform differences and which are drift. This is the
mirror of their
[0002-scoop-bucket-template-comparison](https://github.com/hasansezertasan/copier-homebrew-tap/blob/main/docs/research/0002-scoop-bucket-template-comparison.md),
which diffed us at `052992b` and adopted our mise pins, agent prompt, AGENTS
layout, and drift pull request.

## Method

File-by-file diff, documentation and README content included; auto-generated
files (`CHANGELOG.md`, `cobo.lock`, `release-please-manifest.json`) and
platform-specific files excluded.

## Findings applied here

- Added the missing root `AGENTS.md` (template layout, owner-agnostic rule,
  Cobo byte-identical rule, MADR/research conventions, render-and-check
  command); see [ADR-0000](../adr/0000-use-madr.md).
- Started `docs/adr/` and `docs/research/`; backfilled the load-bearing
  decisions ([ADR-0001](../adr/0001-generate-gitignore-with-cobo.md) through
  [ADR-0007](../adr/0007-optional-workflow-token-for-automated-pull-requests.md)).
  The tap's superseded records (their ADR-0002/0003) were not ported — they
  record history this repository never had.
- Fixed the stale root `README.md` install-status sentence: `scoop-bucket-skills`
  now records one installation each for the Claude Code and Codex plugin routes
  on macOS, installer route none (their research `0003` found the same staleness
  on both sides).
- Added the `release.yml` and `docs/` rows to the root `README.md` layout table.
- Ported the generated-README sections: agent-skills pointer, expanded validate
  steps (`lint`/`style` plus the `prek.toml` gate rationale), automated-PR
  fallbacks with token scopes, `zizmor`/drift notes, and pull request
  conventions.
- Restored the explanatory comments in `check-branch-name.yml`,
  `check-pr-title.yml`, `actionlint.yaml`, and `prek.toml`; added the
  `[tasks.hooks]`/`[tasks.lint]` tasks, the markdownlint MD041 override for the
  PR template, the `-present` copyright range, the `.copier-answers.yml` leading
  `---`, and the binary-files `.editorconfig` block.
- Passed `WORKFLOW_TOKEN` with `GITHUB_TOKEN` fallback to the Cobo drift action,
  matching the update workflows.

## Deliberately not adopted

- Bottle `publish.yml`, `brew test-bot`/`brew audit` CI, and the formula/cask
  split of the update workflows: Homebrew tooling with no Scoop equivalent.
- The Ruby `.gitignore` fragment, `[*.rb]` editorconfig stanza, and `sur` typos
  entry: Ruby/packaging concerns of formulae.
- Their `scripts.yml` workflow split: our `readme.yml` separation exists because
  `tests.yml` ignores `**.md` to skip the Windows install matrix on doc edits;
  their single `scripts.yml` covers the catalog check on README edits directly.
- `python3` command naming and `shellcheck`: their toolchain targets
  macOS/Linux runners; ours targets Windows (`python.exe`, `run_windows`
  blocks).
- The issue-template contact link (Scoop vs Homebrew Discussions) and
  `blank_issues_enabled: false` (already identical): issue policy, not drift.
- Tap-name runtime resolution from the Actions context only: the bucket resolves
  identity from the Git remote, the Actions context, or an explicit override
  (see [ADR-0003](../adr/0003-render-identity-with-copier-and-resolve-at-runtime.md)).
- `uv`/`shellcheck` tool pins vs our `python` pin: per-platform toolchain.
