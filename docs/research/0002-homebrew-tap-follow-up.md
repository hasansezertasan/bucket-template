# Homebrew-tap follow-up: their docs sync from our comparison

Research snapshot: 2026-10-17, against
[hasansezertasan/copier-homebrew-tap](https://github.com/hasansezertasan/copier-homebrew-tap)
at `c50149d` (this repository on `hasansezertasan/chore-compare-homebrew-tap`).
Follow-up to
[0001-homebrew-tap-template-comparison](0001-homebrew-tap-template-comparison.md):
the tap has since recorded its side of the sync in
[0003-docs-sync-from-scoop-comparison](https://github.com/hasansezertasan/copier-homebrew-tap/blob/main/docs/research/0003-docs-sync-from-scoop-comparison.md)
and
[ADR-0010](https://github.com/hasansezertasan/copier-homebrew-tap/blob/main/docs/adr/0010-catalog-provenance-and-manual-test-dispatch.md).
Claims below come from diffing their `main` against this repository file by
file, documentation and README content only; auto-generated files
(`CHANGELOG.md`) and platform-specific files excluded.

## Findings applied here

- Strengthened the generated README's "Add a manifest" section to mirror their
  "Add a package": the skill documents the routes and which generated fields
  are guesses needing a human check, and the section now says plainly not to
  hand-write a manifest.
- Split the `WORKFLOW_TOKEN`/`GITHUB_TOKEN` fallback out of "Automated updates"
  into its own "Automated pull requests" subsection, matching their structure.
- Corrected the `GITHUB_TOKEN` wording in `CONTRIBUTING.md` and the generated
  README: a pull request opened or updated with `GITHUB_TOKEN` gets its
  `pull_request` checks created but held pending approval (maintainers approve
  them or run `Tests` manually); only other token-triggered events are
  suppressed outright. The flat "does not start workflows" phrasing, copied
  from the tap, overstated it. A Codex review then noted the title and
  branch-name lint gates listen on `pull_request_target`, which starts no run
  at all for these pull requests — both files now say approval alone does not
  run them and a push or close/reopen still triggers them.
- Ported their `template/AGENTS.md` polish: `tests/` in the Layout section, the
  "CI fails a stale catalog table" consequence, and the "which generated
  fields need a human check" pointer.
- Named the `scoop-add` skill from `hasansezertasan/scoop-bucket-skills` in
  `copier.yml`'s post-copy message, mirroring their `homebrew-add` pointer.
- Fixed `docs/adr/0005` paths to the `template/`-prefixed, repository-relative
  form the root `README.md` layout table promises. Their layout row reads the
  opposite way ("relative to a generated tap"), which is correct for their
  records — the two rows describe different conventions, not a contradiction
  to resolve by copying.

## Deliberately not adopted

- Their ADR-0010 catalog items needed no port: our packages table already has
  the type-derived `Source` column theirs was copied from, and our generator
  already uses explicit `encoding="utf-8"`, reports `--check` on stderr, and
  points at `mise run generate-readme`.
- Their `workflow_dispatch` fallback for suppressed checks needed no port:
  `tests.yml` and `readme.yml` already carry it.
- Their ADR-0008 (inline-shell update workflows) confirms our opposite choice
  ([ADR-0005](../adr/0005-update-manifests-as-a-tested-python-script.md)):
  Scoop has no `brew bump-formula-pr`, so the tested-script rationale stands.
- Bottle `publish.yml`, `brew test-bot`/`brew audit` CI, the Ruby `.gitignore`
  fragment, `[*.rb]` editorconfig stanza, and `sur` typos entry: packaging
  concerns of formulae with no bucket equivalent.
