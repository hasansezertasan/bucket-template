# Keep Agent Skills in a Separate Repository

## Context and Problem Statement

Operating a bucket (adding, fixing, triaging, removing, and verifying
manifests) needs agent skills with judgment: scaffolders for the three install
routes, and which generated fields are guesses that need a human check. If those
skills live in this template, every generated bucket inherits them, and the
scaffolders they drive get copied into every bucket instead of versioned once.

## Considered Options

* Keep the skills and the scaffolders in the template
* Keep the skills in a dedicated repository that also installs as a Claude Code
  or Codex plugin, and reference it from the template
* Ship no skills and document the manifest formats by hand

## Decision Outcome

Chosen option: "Keep the skills in a separate repository." Skills for operating
a generated bucket live in
[`scoop-bucket-skills`](https://github.com/hasansezertasan/scoop-bucket-skills),
not here. The template references them from `template/AGENTS.md`, the generated
`README.md` (`scoop-add` scaffolder, run-directly pointer), and the root
`README.md` agent prompt. The `scoop-add` scaffolder infers the bucket's GitHub
repository from the `origin` remote, so generated buckets need no identity
placeholders for it.

### Consequences

* Good, because skill improvements ship once instead of fanning out through
  `copier update` into every bucket.
* Good, because generated buckets stay free of skill maintenance burden.
* Bad, because the template depends on an external repository that must stay
  aligned with the manifest layouts here.
